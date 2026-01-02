"""AWS Glue ETL Job: JSON to Apache Parquet Transformation.

This script transforms JSON documents to Apache Parquet format
with Snappy compression for optimal query performance in Athena.

Performance Benefits:
- Columnar storage enables predicate pushdown
- 2x faster to unload vs row-based formats
- 6x less storage with Snappy compression
- Partition pruning for time-based queries

Usage:
    This script is executed by AWS Glue as a PySpark job.
    Arguments are passed via --key=value format.

Arguments:
    --source_path: S3 path for input JSON files
    --target_path: S3 path for output Parquet files
    --partition_year: Year partition value
    --partition_month: Month partition value
    --partition_day: Day partition value
    --partition_hour: Hour partition value (optional)
    --database: Glue database name
    --table_name: Target table name
"""

import sys
from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from awsglue.job import Job
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.types import TimestampType

# Initialize Glue context
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)

# Get job arguments
args = getResolvedOptions(
    sys.argv,
    [
        "JOB_NAME",
        "source_path",
        "target_path",
        "partition_year",
        "partition_month",
        "partition_day",
        "partition_hour",
        "database",
        "table_name",
    ],
)

job.init(args["JOB_NAME"], args)

# Extract arguments
source_path = args["source_path"]
target_path = args["target_path"]
partition_year = args["partition_year"]
partition_month = args["partition_month"]
partition_day = args["partition_day"]
partition_hour = args.get("partition_hour", "00")
database = args["database"]
table_name = args["table_name"]

print(f"ETL Job Starting")
print(f"Source: {source_path}")
print(f"Target: {target_path}")
print(f"Partition: year={partition_year}/month={partition_month}/day={partition_day}/hour={partition_hour}")


def read_json_data(path: str) -> DynamicFrame:
    """Read JSON data from S3.

    Reads newline-delimited JSON (NDJSON) files from the specified path.

    Args:
        path: S3 path to JSON files

    Returns:
        DynamicFrame containing parsed JSON records
    """
    print(f"Reading JSON data from: {path}")

    dynamic_frame = glueContext.create_dynamic_frame.from_options(
        connection_type="s3",
        connection_options={
            "paths": [path],
            "recurse": True,
        },
        format="json",
        format_options={
            "multiLine": False,
            "withHeader": False,
        },
    )

    count = dynamic_frame.count()
    print(f"Read {count} records from source")

    return dynamic_frame


def transform_data(dynamic_frame: DynamicFrame) -> DynamicFrame:
    """Apply transformations to the data.

    Transformations:
    - Add partition columns
    - Cast timestamp fields
    - Flatten nested structures if needed
    - Handle null values

    Args:
        dynamic_frame: Input DynamicFrame

    Returns:
        Transformed DynamicFrame
    """
    print("Applying transformations")

    # Convert to Spark DataFrame for complex transformations
    df = dynamic_frame.toDF()

    # Add partition columns
    df = df.withColumn("year", F.lit(partition_year))
    df = df.withColumn("month", F.lit(partition_month))
    df = df.withColumn("day", F.lit(partition_day))
    df = df.withColumn("hour", F.lit(partition_hour))

    # Ensure timestamp field is properly typed
    if "timestamp" in df.columns:
        df = df.withColumn(
            "timestamp",
            F.to_timestamp(F.col("timestamp"))
        )

    # Handle nested 'properties' field - flatten if small, keep as map otherwise
    if "properties" in df.columns:
        # Keep as map/struct for flexibility
        pass

    # Handle nested 'geo' field
    if "geo" in df.columns:
        # Keep as map/struct for flexibility
        pass

    # Remove any completely null rows
    df = df.na.drop(how="all")

    print(f"Transformed {df.count()} records")

    # Convert back to DynamicFrame
    return DynamicFrame.fromDF(df, glueContext, "transformed_data")


def apply_schema_mapping(dynamic_frame: DynamicFrame) -> DynamicFrame:
    """Apply schema mapping for consistent column types.

    Ensures data types are optimized for Parquet storage
    and Athena query performance.

    Args:
        dynamic_frame: Input DynamicFrame

    Returns:
        DynamicFrame with mapped schema
    """
    print("Applying schema mapping")

    # Apply mappings for known fields
    mappings = [
        ("event_id", "string", "event_id", "string"),
        ("timestamp", "timestamp", "timestamp", "timestamp"),
        ("event_type", "string", "event_type", "string"),
        ("user_id", "string", "user_id", "string"),
        ("session_id", "string", "session_id", "string"),
        ("properties", "struct", "properties", "struct"),
        ("geo", "struct", "geo", "struct"),
        ("year", "string", "year", "string"),
        ("month", "string", "month", "string"),
        ("day", "string", "day", "string"),
        ("hour", "string", "hour", "string"),
    ]

    # Apply mapping - only for fields that exist
    df = dynamic_frame.toDF()
    existing_fields = set(df.columns)

    applicable_mappings = [
        m for m in mappings if m[0] in existing_fields
    ]

    if applicable_mappings:
        return ApplyMapping.apply(
            frame=dynamic_frame,
            mappings=applicable_mappings,
        )

    return dynamic_frame


def write_parquet_data(dynamic_frame: DynamicFrame, path: str) -> None:
    """Write data to S3 in Parquet format with Snappy compression.

    Parquet benefits for Athena:
    - Columnar storage supports predicate pushdown
    - Only reads columns needed for query
    - Snappy compression: ~6x size reduction
    - 2x faster to unload than row formats

    Args:
        dynamic_frame: Data to write
        path: Target S3 path
    """
    print(f"Writing Parquet data to: {path}")

    # Write with Snappy compression and partitioning
    glueContext.write_dynamic_frame.from_options(
        frame=dynamic_frame,
        connection_type="s3",
        connection_options={
            "path": path,
            "partitionKeys": ["year", "month", "day", "hour"],
        },
        format="parquet",
        format_options={
            "compression": "snappy",
            "useGlueParquetWriter": True,
        },
    )

    print("Write complete")


def update_catalog(dynamic_frame: DynamicFrame) -> None:
    """Update AWS Glue Data Catalog with new data.

    Creates or updates table in the Glue catalog for
    Lake Formation and Athena integration.

    Args:
        dynamic_frame: Data frame with schema information
    """
    print(f"Updating catalog: {database}.{table_name}")

    # Write to catalog (creates table if not exists)
    glueContext.write_dynamic_frame.from_catalog(
        frame=dynamic_frame,
        database=database,
        table_name=table_name,
        additional_options={
            "enableUpdateCatalog": True,
            "updateBehavior": "UPDATE_IN_DATABASE",
            "partitionKeys": ["year", "month", "day", "hour"],
        },
    )

    print("Catalog updated")


def main():
    """Main ETL job execution."""
    print("=" * 60)
    print("AWS Glue ETL: JSON to Parquet Transformation")
    print("=" * 60)

    try:
        # Read source JSON data
        source_data = read_json_data(source_path)

        if source_data.count() == 0:
            print("No data found in source path. Skipping transformation.")
            job.commit()
            return

        # Transform data
        transformed_data = transform_data(source_data)

        # Apply schema mapping
        mapped_data = apply_schema_mapping(transformed_data)

        # Write to Parquet with Snappy compression
        write_parquet_data(mapped_data, target_path)

        # Update Glue catalog
        update_catalog(mapped_data)

        print("=" * 60)
        print("ETL Job Completed Successfully")
        print("=" * 60)

    except Exception as e:
        print(f"ETL Job Failed: {e}")
        raise

    finally:
        job.commit()


if __name__ == "__main__":
    main()
