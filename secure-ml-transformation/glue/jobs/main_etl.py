"""Main ETL Job for Secure ML Data Transformation.

This Glue ETL job orchestrates the complete data transformation pipeline:
1. PII Tokenization
2. Transaction Amount Binning
3. Merchant Category Encoding
4. Anomaly Detection

It runs within a VPC without internet access and maintains full audit trails.
"""

import json
import sys
from datetime import datetime
from typing import Any

from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from awsglue.job import Job
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F

# Import transformation modules
from amount_binning import create_binner
from anomaly_detection import create_detector
from merchant_encoding import create_encoder
from pii_tokenization import create_tokenizer


def main():
    """Main entry point for the Glue ETL job."""

    # Parse job parameters
    args = getResolvedOptions(
        sys.argv,
        [
            "JOB_NAME",
            "source_bucket",
            "target_bucket",
            "source_path",
            "environment",
            "pii_salt",
            "pii_columns",
            "binning_method",
            "binning_percentiles",
            "contamination",
            "merchant_mapping_path",
            "enable_job_bookmark",
        ],
    )

    # Initialize Glue context
    sc = SparkContext()
    glue_context = GlueContext(sc)
    spark = glue_context.spark_session
    job = Job(glue_context)
    job.init(args["JOB_NAME"], args)

    logger = glue_context.get_logger()
    logger.info(f"Starting ETL job: {args['JOB_NAME']}")
    logger.info(f"Environment: {args['environment']}")

    # Record job start time for lineage
    job_start_time = datetime.utcnow()
    job_run_id = args.get("JOB_RUN_ID", "unknown")

    try:
        # =====================================================================
        # Step 1: Read source data
        # =====================================================================
        logger.info(f"Reading data from: {args['source_path']}")

        # Use job bookmarks for incremental processing
        source_dyf = glue_context.create_dynamic_frame.from_options(
            connection_type="s3",
            connection_options={
                "paths": [args["source_path"]],
                "recurse": True,
            },
            format="parquet",
            transformation_ctx="source_data",
        )

        # Convert to DataFrame for transformations
        df = source_dyf.toDF()
        input_count = df.count()
        logger.info(f"Read {input_count} records")

        if input_count == 0:
            logger.info("No new data to process")
            job.commit()
            return

        # =====================================================================
        # Step 2: PII Tokenization
        # =====================================================================
        logger.info("Starting PII tokenization")

        pii_columns = args.get("pii_columns", "customer_id,account_number,email").split(
            ","
        )
        pii_salt = args.get("pii_salt", "default_salt_change_in_production")

        tokenizer = create_tokenizer(salt=pii_salt, logger=logger)

        # Configure tokenization for each column
        pii_configs = []
        for col in pii_columns:
            col = col.strip()
            if col in df.columns:
                if col in ["card_number"]:
                    pii_configs.append(
                        {
                            "column_name": col,
                            "method": "format_preserving",
                            "preserve_prefix": 4,
                            "preserve_suffix": 4,
                        }
                    )
                elif col in ["email", "phone"]:
                    pii_configs.append({"column_name": col, "method": "hash"})
                else:
                    pii_configs.append(
                        {
                            "column_name": col,
                            "method": "deterministic",
                            "output_length": 16,
                        }
                    )

        df = tokenizer.tokenize_dataframe(df, pii_configs)

        # Log PII audit event
        _log_audit_event(
            glue_context,
            job_run_id,
            "PII_TOKENIZATION",
            {
                "columns_tokenized": [c["column_name"] for c in pii_configs],
                "records_processed": input_count,
            },
        )

        # =====================================================================
        # Step 3: Transaction Amount Binning
        # =====================================================================
        logger.info("Starting amount binning")

        binner = create_binner(logger=logger)

        binning_method = args.get("binning_method", "percentile")
        percentiles_str = args.get("binning_percentiles", "0,10,25,50,75,90,95,99,100")
        percentiles = [int(p.strip()) for p in percentiles_str.split(",")]

        df = binner.bin_amounts(
            df,
            column="transaction_amount",
            method=binning_method,
            percentiles=percentiles,
            labels=[
                "micro",
                "small",
                "low",
                "medium",
                "high",
                "large",
                "very_large",
                "extreme",
            ],
        )

        logger.info("Amount binning complete")

        # =====================================================================
        # Step 4: Merchant Category Encoding
        # =====================================================================
        logger.info("Starting merchant encoding")

        encoder = create_encoder(logger=logger)

        # Load custom mappings from S3 if provided
        mapping_path = args.get("merchant_mapping_path")
        if mapping_path:
            try:
                encoder.load_mappings_from_s3(spark, mapping_path)
            except Exception as e:
                logger.warn(f"Could not load custom mappings: {e}, using defaults")

        df = encoder.encode_merchants(df, mcc_column="merchant_category_code")

        # Log unknown MCCs for future mapping updates
        unknown_mccs = encoder.get_unknown_mccs(df, "merchant_category_code")
        unknown_count = unknown_mccs.count()
        if unknown_count > 0:
            logger.warn(f"Found {unknown_count} unknown MCC codes")
            # Optionally write unknown MCCs to S3 for analysis
            unknown_mccs.write.mode("overwrite").parquet(
                f"s3://{args['target_bucket']}/metadata/unknown_mccs/{job_run_id}/"
            )

        logger.info("Merchant encoding complete")

        # =====================================================================
        # Step 5: Anomaly Detection
        # =====================================================================
        logger.info("Starting anomaly detection")

        detector = create_detector(
            contamination=float(args.get("contamination", "0.01")),
            n_estimators=100,
            logger=logger,
        )

        # Add temporal features
        df = detector.add_temporal_features(df, "transaction_timestamp")

        # Add velocity features
        df = detector.add_velocity_features(
            df,
            customer_column="customer_id",
            timestamp_column="transaction_timestamp",
            amount_column="transaction_amount",
        )

        # Define features for anomaly detection
        anomaly_features = [
            "transaction_amount_bin_encoded",
            "merchant_risk_score",
            "hour_of_day",
            "day_of_week",
            "is_weekend",
            "is_night",
            "amount_deviation",
        ]

        # Filter to only existing columns
        anomaly_features = [f for f in anomaly_features if f in df.columns]

        if len(anomaly_features) >= 2:
            df = detector.detect_anomalies(df, anomaly_features)
        else:
            logger.warn("Insufficient features for anomaly detection")
            df = df.withColumn("anomaly_score", F.lit(0.0))
            df = df.withColumn("is_anomaly", F.lit(False))
            df = df.withColumn("anomaly_percentile", F.lit(50.0))

        anomaly_count = df.filter(F.col("is_anomaly")).count()
        logger.info(f"Detected {anomaly_count} anomalies")

        # Log anomaly audit event
        _log_audit_event(
            glue_context,
            job_run_id,
            "ANOMALY_DETECTED",
            {
                "anomaly_count": anomaly_count,
                "total_records": input_count,
                "anomaly_rate": anomaly_count / input_count if input_count > 0 else 0,
            },
        )

        # =====================================================================
        # Step 6: Write Output
        # =====================================================================
        logger.info("Writing transformed data")

        output_count = df.count()

        # Partition output by date
        df = df.withColumn(
            "processing_date", F.to_date(F.current_timestamp())
        )

        # Convert back to DynamicFrame
        output_dyf = DynamicFrame.fromDF(df, glue_context, "output_data")

        # Write to S3 with encryption
        output_path = f"s3://{args['target_bucket']}/ml-ready/"

        glue_context.write_dynamic_frame.from_options(
            frame=output_dyf,
            connection_type="s3",
            connection_options={
                "path": output_path,
                "partitionKeys": ["processing_date"],
            },
            format="parquet",
            format_options={
                "compression": "snappy",
            },
            transformation_ctx="write_output",
        )

        logger.info(f"Wrote {output_count} records to {output_path}")

        # =====================================================================
        # Step 7: Record Lineage
        # =====================================================================
        job_end_time = datetime.utcnow()

        lineage_record = {
            "job_execution_id": job_run_id,
            "job_name": args["JOB_NAME"],
            "start_time": job_start_time.isoformat(),
            "end_time": job_end_time.isoformat(),
            "status": "SUCCEEDED",
            "input_records": input_count,
            "output_records": output_count,
            "filtered_records": input_count - output_count,
            "transformations_applied": [
                "pii_tokenization",
                "amount_binning",
                "merchant_encoding",
                "anomaly_detection",
            ],
            "input_paths": [args["source_path"]],
            "output_paths": [output_path],
            "parameters": {
                "binning_method": binning_method,
                "contamination": args.get("contamination", "0.01"),
                "pii_columns": pii_columns,
            },
        }

        # Write lineage to S3
        lineage_df = spark.createDataFrame([lineage_record])
        lineage_df.write.mode("overwrite").json(
            f"s3://{args['target_bucket']}/lineage/{job_run_id}/"
        )

        logger.info("Job completed successfully")

        # Commit job (updates bookmarks)
        job.commit()

    except Exception as e:
        logger.error(f"Job failed: {str(e)}")

        # Log failure
        _log_audit_event(
            glue_context,
            job_run_id,
            "JOB_FAILED",
            {"error": str(e)},
        )

        raise


def _log_audit_event(
    glue_context: GlueContext,
    job_run_id: str,
    event_type: str,
    details: dict[str, Any],
) -> None:
    """Log an audit event.

    Args:
        glue_context: Glue context for logging
        job_run_id: Current job run ID
        event_type: Type of audit event
        details: Event details
    """
    logger = glue_context.get_logger()

    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "job_execution_id": job_run_id,
        "details": details,
    }

    logger.info(f"AUDIT: {json.dumps(audit_entry)}")


if __name__ == "__main__":
    main()
