"""Merchant Category Encoding module for Glue ETL jobs.

This module provides functions for encoding merchant category codes (MCC)
into ML-friendly features with custom mappings and risk scoring.
"""

import json
from typing import Any

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import (
    BooleanType,
    FloatType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)


class MerchantEncoder:
    """Merchant category encoding handler for PySpark DataFrames."""

    # Default MCC mappings for common categories
    DEFAULT_MAPPINGS = {
        "5411": {
            "category": "grocery_stores",
            "category_id": 1,
            "risk_level": "low",
            "risk_score": 0.1,
            "parent_category": "retail",
            "is_cash_equivalent": False,
        },
        "5812": {
            "category": "eating_places_restaurants",
            "category_id": 2,
            "risk_level": "medium",
            "risk_score": 0.3,
            "parent_category": "dining",
            "is_cash_equivalent": False,
        },
        "5814": {
            "category": "fast_food_restaurants",
            "category_id": 3,
            "risk_level": "low",
            "risk_score": 0.2,
            "parent_category": "dining",
            "is_cash_equivalent": False,
        },
        "5912": {
            "category": "drug_stores_pharmacies",
            "category_id": 4,
            "risk_level": "low",
            "risk_score": 0.1,
            "parent_category": "healthcare",
            "is_cash_equivalent": False,
        },
        "5311": {
            "category": "department_stores",
            "category_id": 5,
            "risk_level": "low",
            "risk_score": 0.15,
            "parent_category": "retail",
            "is_cash_equivalent": False,
        },
        "5541": {
            "category": "service_stations",
            "category_id": 6,
            "risk_level": "medium",
            "risk_score": 0.35,
            "parent_category": "automotive",
            "is_cash_equivalent": False,
        },
        "5942": {
            "category": "book_stores",
            "category_id": 7,
            "risk_level": "low",
            "risk_score": 0.1,
            "parent_category": "retail",
            "is_cash_equivalent": False,
        },
        "6011": {
            "category": "atm_cash_disbursements",
            "category_id": 8,
            "risk_level": "high",
            "risk_score": 0.7,
            "parent_category": "financial",
            "is_cash_equivalent": True,
        },
        "6012": {
            "category": "financial_institutions",
            "category_id": 9,
            "risk_level": "high",
            "risk_score": 0.65,
            "parent_category": "financial",
            "is_cash_equivalent": True,
        },
        "7011": {
            "category": "hotels_motels_resorts",
            "category_id": 10,
            "risk_level": "medium",
            "risk_score": 0.4,
            "parent_category": "travel",
            "is_cash_equivalent": False,
        },
        "4511": {
            "category": "airlines",
            "category_id": 11,
            "risk_level": "medium",
            "risk_score": 0.45,
            "parent_category": "travel",
            "is_cash_equivalent": False,
        },
        "7995": {
            "category": "gambling",
            "category_id": 12,
            "risk_level": "critical",
            "risk_score": 0.9,
            "parent_category": "entertainment",
            "is_cash_equivalent": True,
        },
        "5999": {
            "category": "miscellaneous_retail",
            "category_id": 13,
            "risk_level": "medium",
            "risk_score": 0.5,
            "parent_category": "retail",
            "is_cash_equivalent": False,
        },
    }

    DEFAULT_CATEGORY = {
        "category": "unknown",
        "category_id": 999,
        "risk_level": "high",
        "risk_score": 0.8,
        "parent_category": "uncategorized",
        "is_cash_equivalent": False,
    }

    def __init__(
        self,
        mappings: dict[str, dict[str, Any]] | None = None,
        default_category: dict[str, Any] | None = None,
        logger: Any = None,
    ) -> None:
        """Initialize the encoder.

        Args:
            mappings: Custom MCC to category mappings
            default_category: Default category for unknown MCCs
            logger: Optional Glue logger
        """
        self.mappings = mappings or self.DEFAULT_MAPPINGS
        self.default_category = default_category or self.DEFAULT_CATEGORY
        self.logger = logger

    def encode_merchants(
        self,
        df: DataFrame,
        mcc_column: str = "merchant_category_code",
    ) -> DataFrame:
        """Encode merchant category codes.

        Args:
            df: Input DataFrame
            mcc_column: Column containing MCC codes

        Returns:
            DataFrame with encoded merchant features
        """
        if mcc_column not in df.columns:
            if self.logger:
                self.logger.warn(f"Column {mcc_column} not found in DataFrame")
            return df

        # Broadcast mappings for efficient lookup
        mappings_json = json.dumps(self.mappings)
        default_json = json.dumps(self.default_category)

        # Create UDFs for each output column
        @F.udf(returnType=StringType())
        def get_category(mcc: str) -> str:
            mappings = json.loads(mappings_json)
            default = json.loads(default_json)
            if mcc and mcc in mappings:
                return mappings[mcc]["category"]
            return default["category"]

        @F.udf(returnType=IntegerType())
        def get_category_id(mcc: str) -> int:
            mappings = json.loads(mappings_json)
            default = json.loads(default_json)
            if mcc and mcc in mappings:
                return mappings[mcc]["category_id"]
            return default["category_id"]

        @F.udf(returnType=StringType())
        def get_risk_level(mcc: str) -> str:
            mappings = json.loads(mappings_json)
            default = json.loads(default_json)
            if mcc and mcc in mappings:
                return mappings[mcc]["risk_level"]
            return default["risk_level"]

        @F.udf(returnType=FloatType())
        def get_risk_score(mcc: str) -> float:
            mappings = json.loads(mappings_json)
            default = json.loads(default_json)
            if mcc and mcc in mappings:
                return float(mappings[mcc]["risk_score"])
            return float(default["risk_score"])

        @F.udf(returnType=StringType())
        def get_parent_category(mcc: str) -> str:
            mappings = json.loads(mappings_json)
            default = json.loads(default_json)
            if mcc and mcc in mappings:
                return mappings[mcc]["parent_category"]
            return default["parent_category"]

        @F.udf(returnType=BooleanType())
        def get_is_cash_equivalent(mcc: str) -> bool:
            mappings = json.loads(mappings_json)
            default = json.loads(default_json)
            if mcc and mcc in mappings:
                return mappings[mcc]["is_cash_equivalent"]
            return default["is_cash_equivalent"]

        # Apply all encodings
        result_df = df.withColumn("merchant_category", get_category(F.col(mcc_column)))
        result_df = result_df.withColumn(
            "merchant_category_id", get_category_id(F.col(mcc_column))
        )
        result_df = result_df.withColumn(
            "merchant_risk_level", get_risk_level(F.col(mcc_column))
        )
        result_df = result_df.withColumn(
            "merchant_risk_score", get_risk_score(F.col(mcc_column))
        )
        result_df = result_df.withColumn(
            "merchant_parent_category", get_parent_category(F.col(mcc_column))
        )
        result_df = result_df.withColumn(
            "is_cash_equivalent", get_is_cash_equivalent(F.col(mcc_column))
        )

        # Encode risk level numerically
        result_df = result_df.withColumn(
            "merchant_risk_encoded",
            F.when(F.col("merchant_risk_level") == "low", 0)
            .when(F.col("merchant_risk_level") == "medium", 1)
            .when(F.col("merchant_risk_level") == "high", 2)
            .when(F.col("merchant_risk_level") == "critical", 3)
            .otherwise(2),
        )

        if self.logger:
            self.logger.info(
                f"Encoded {df.count()} records with merchant categories"
            )

        return result_df

    def load_mappings_from_s3(
        self,
        spark_session: Any,
        s3_path: str,
    ) -> None:
        """Load custom mappings from S3.

        Args:
            spark_session: Spark session
            s3_path: S3 path to JSON mappings file
        """
        try:
            mappings_df = spark_session.read.json(s3_path)
            mappings_dict = {}

            for row in mappings_df.collect():
                mcc = row["mcc"]
                mappings_dict[mcc] = {
                    "category": row["category"],
                    "category_id": row["category_id"],
                    "risk_level": row["risk_level"],
                    "risk_score": row["risk_score"],
                    "parent_category": row["parent_category"],
                    "is_cash_equivalent": row["is_cash_equivalent"],
                }

            self.mappings = mappings_dict

            if self.logger:
                self.logger.info(f"Loaded {len(mappings_dict)} mappings from S3")

        except Exception as e:
            if self.logger:
                self.logger.warn(f"Failed to load mappings from S3: {e}, using defaults")

    def get_unknown_mccs(self, df: DataFrame, mcc_column: str) -> DataFrame:
        """Get MCCs not in the mapping.

        Args:
            df: Input DataFrame
            mcc_column: Column containing MCC codes

        Returns:
            DataFrame with unknown MCCs and their counts
        """
        known_mccs = list(self.mappings.keys())

        unknown_df = (
            df.filter(~F.col(mcc_column).isin(known_mccs))
            .groupBy(mcc_column)
            .count()
            .orderBy(F.desc("count"))
        )

        return unknown_df


def create_encoder(
    mappings: dict[str, dict[str, Any]] | None = None,
    default_category: dict[str, Any] | None = None,
    logger: Any = None,
) -> MerchantEncoder:
    """Factory function to create an encoder instance.

    Args:
        mappings: Custom MCC mappings
        default_category: Default category config
        logger: Optional Glue logger

    Returns:
        Configured MerchantEncoder instance
    """
    return MerchantEncoder(
        mappings=mappings,
        default_category=default_category,
        logger=logger,
    )
