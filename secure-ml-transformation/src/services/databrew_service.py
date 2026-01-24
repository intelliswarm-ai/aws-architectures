"""Service for AWS Glue DataBrew operations."""

from typing import Any

import boto3
from aws_lambda_powertools import Logger
from botocore.config import Config

from src.common.config import get_settings

logger = Logger()


class DataBrewService:
    """Service for interacting with AWS Glue DataBrew."""

    def __init__(self) -> None:
        """Initialize DataBrew service."""
        self._settings = get_settings()
        self._client = boto3.client(
            "databrew",
            region_name=self._settings.aws_region,
            config=Config(
                retries={"max_attempts": 3, "mode": "adaptive"},
            ),
        )

    def create_profile_job(
        self,
        job_name: str,
        dataset_name: str,
        output_bucket: str,
        output_prefix: str,
    ) -> str:
        """Create a DataBrew profile job for PII detection.

        Args:
            job_name: Name for the profile job
            dataset_name: Name of the DataBrew dataset
            output_bucket: S3 bucket for profile output
            output_prefix: S3 prefix for profile output

        Returns:
            Profile job name
        """
        try:
            response = self._client.create_profile_job(
                Name=job_name,
                DatasetName=dataset_name,
                OutputLocation={
                    "Bucket": output_bucket,
                    "Key": output_prefix,
                },
                RoleArn=f"arn:aws:iam::{self._get_account_id()}:role/{self._settings.resource_prefix}-databrew-role",
                Configuration={
                    "DatasetStatisticsConfiguration": {
                        "IncludedStatistics": [
                            "CORRELATION",
                            "DISTRIBUTION",
                            "DUPLICATE_ROWS",
                            "MISSING",
                            "OUTLIER",
                        ],
                    },
                    "ProfileColumns": [
                        {"Regex": ".*"},  # Profile all columns
                    ],
                    "EntityDetectorConfiguration": {
                        "EntityTypes": [
                            "USA_SSN",
                            "EMAIL",
                            "PHONE_NUMBER",
                            "CREDIT_CARD",
                            "IP_ADDRESS",
                            "DATE",
                            "USA_PASSPORT_NUMBER",
                        ],
                    },
                },
                Tags={
                    "Project": self._settings.project_name,
                    "Environment": self._settings.environment,
                },
            )

            logger.info(
                "Profile job created",
                extra={"job_name": job_name, "dataset": dataset_name},
            )

            return response["Name"]

        except Exception as e:
            logger.exception("Failed to create profile job")
            raise

    def run_profile_job(self, job_name: str) -> str:
        """Start a DataBrew profile job run.

        Args:
            job_name: Name of the profile job

        Returns:
            Run ID
        """
        try:
            response = self._client.start_job_run(Name=job_name)
            run_id = response["RunId"]

            logger.info(
                "Profile job started",
                extra={"job_name": job_name, "run_id": run_id},
            )

            return run_id

        except Exception as e:
            logger.exception("Failed to start profile job")
            raise

    def get_profile_results(
        self,
        job_name: str,
        run_id: str,
    ) -> dict[str, Any]:
        """Get results from a profile job run.

        Args:
            job_name: Name of the profile job
            run_id: Run ID

        Returns:
            Profile results including PII detection
        """
        try:
            response = self._client.describe_job_run(
                Name=job_name,
                RunId=run_id,
            )

            return {
                "status": response["State"],
                "started": response.get("StartedOn"),
                "completed": response.get("CompletedOn"),
                "outputs": response.get("Outputs", []),
                "data_catalog_outputs": response.get("DataCatalogOutputs", []),
            }

        except Exception as e:
            logger.exception("Failed to get profile results")
            raise

    def create_pii_recipe(
        self,
        recipe_name: str,
        pii_columns: list[dict[str, Any]],
    ) -> str:
        """Create a DataBrew recipe for PII handling.

        Args:
            recipe_name: Name for the recipe
            pii_columns: List of PII column configurations

        Returns:
            Recipe name
        """
        steps = []

        for col_config in pii_columns:
            column_name = col_config["column_name"]
            method = col_config.get("method", "REDACT")

            if method == "REDACT":
                steps.append(
                    {
                        "Action": {
                            "Operation": "REPLACE_VALUE",
                            "Parameters": {
                                "sourceColumn": column_name,
                                "pattern": ".*",
                                "value": "***REDACTED***",
                            },
                        },
                    }
                )
            elif method == "HASH":
                steps.append(
                    {
                        "Action": {
                            "Operation": "CRYPTOGRAPHIC_HASH",
                            "Parameters": {
                                "sourceColumn": column_name,
                                "targetColumn": f"{column_name}_hashed",
                            },
                        },
                    }
                )
            elif method == "MASK":
                preserve_chars = col_config.get("preserve_chars", 4)
                steps.append(
                    {
                        "Action": {
                            "Operation": "MASK_CUSTOM",
                            "Parameters": {
                                "sourceColumn": column_name,
                                "maskValue": "*",
                                "startIndex": str(preserve_chars),
                            },
                        },
                    }
                )

        try:
            response = self._client.create_recipe(
                Name=recipe_name,
                Steps=steps,
                Tags={
                    "Project": self._settings.project_name,
                    "Environment": self._settings.environment,
                },
            )

            logger.info(
                "PII recipe created",
                extra={
                    "recipe_name": recipe_name,
                    "step_count": len(steps),
                },
            )

            return response["Name"]

        except Exception as e:
            logger.exception("Failed to create PII recipe")
            raise

    def create_dataset(
        self,
        dataset_name: str,
        s3_bucket: str,
        s3_key: str,
        format_type: str = "PARQUET",
    ) -> str:
        """Create a DataBrew dataset from S3.

        Args:
            dataset_name: Name for the dataset
            s3_bucket: S3 bucket containing data
            s3_key: S3 key or prefix
            format_type: Data format (PARQUET, CSV, JSON)

        Returns:
            Dataset name
        """
        try:
            input_config: dict[str, Any] = {
                "S3InputDefinition": {
                    "Bucket": s3_bucket,
                    "Key": s3_key,
                }
            }

            format_options: dict[str, Any] = {}
            if format_type == "CSV":
                format_options = {
                    "Csv": {
                        "Delimiter": ",",
                        "HeaderRow": True,
                    }
                }
            elif format_type == "JSON":
                format_options = {
                    "Json": {
                        "MultiLine": False,
                    }
                }

            response = self._client.create_dataset(
                Name=dataset_name,
                Input=input_config,
                Format=format_type,
                FormatOptions=format_options if format_options else None,
                Tags={
                    "Project": self._settings.project_name,
                    "Environment": self._settings.environment,
                },
            )

            logger.info(
                "Dataset created",
                extra={
                    "dataset_name": dataset_name,
                    "bucket": s3_bucket,
                    "format": format_type,
                },
            )

            return response["Name"]

        except Exception as e:
            logger.exception("Failed to create dataset")
            raise

    def _get_account_id(self) -> str:
        """Get current AWS account ID."""
        sts = boto3.client("sts", region_name=self._settings.aws_region)
        return sts.get_caller_identity()["Account"]
