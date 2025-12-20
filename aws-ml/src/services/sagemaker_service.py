"""SageMaker service for ML inference and training."""

import json
import time
from typing import Any

from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError

from src.common.clients import get_clients
from src.common.config import get_settings
from src.common.exceptions import InferenceError, NonRetryableError, RetryableError
from src.common.models import InferenceResult

logger = Logger()


class SageMakerService:
    """Service for SageMaker inference and training operations."""

    def __init__(self):
        self.settings = get_settings()
        self.clients = get_clients()

    def invoke_endpoint(
        self,
        document_id: str,
        features: dict[str, Any],
        endpoint_name: str | None = None,
        content_type: str = "application/json",
    ) -> InferenceResult:
        """
        Invoke SageMaker endpoint for real-time inference.
        """
        endpoint = endpoint_name or self.settings.sagemaker_endpoint_name

        if not endpoint:
            raise InferenceError(
                "SageMaker endpoint name not configured",
                document_id=document_id,
            )

        try:
            start_time = time.time()

            # Serialize input
            body = json.dumps(features)

            # Invoke endpoint
            response = self.clients.sagemaker_runtime.invoke_endpoint(
                EndpointName=endpoint,
                ContentType=content_type,
                Accept="application/json",
                Body=body,
            )

            latency_ms = (time.time() - start_time) * 1000

            # Parse response
            result = json.loads(response["Body"].read().decode("utf-8"))

            return self._parse_inference_result(document_id, result, latency_ms)

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ModelError":
                raise InferenceError(
                    f"Model inference error: {e}",
                    document_id=document_id,
                    model_name=endpoint,
                )
            if error_code in ("ThrottlingException", "ServiceUnavailable"):
                raise RetryableError(
                    f"SageMaker endpoint throttled: {e}",
                    document_id=document_id,
                    retry_after_seconds=5,
                )
            raise InferenceError(
                f"SageMaker invocation failed: {e}",
                document_id=document_id,
                model_name=endpoint,
            )

    def invoke_endpoint_async(
        self,
        document_id: str,
        features: dict[str, Any],
        endpoint_name: str | None = None,
        input_location: str | None = None,
    ) -> str:
        """
        Invoke SageMaker async endpoint.
        Returns output location for polling.
        """
        endpoint = endpoint_name or self.settings.sagemaker_endpoint_name

        try:
            body = json.dumps(features)

            response = self.clients.sagemaker_runtime.invoke_endpoint_async(
                EndpointName=endpoint,
                ContentType="application/json",
                Accept="application/json",
                InputLocation=input_location,
                InvocationTimeoutSeconds=300,
            )

            output_location = response.get("OutputLocation", "")
            logger.info(
                "Started async inference",
                document_id=document_id,
                output_location=output_location,
            )
            return output_location

        except ClientError as e:
            raise InferenceError(
                f"Async invocation failed: {e}",
                document_id=document_id,
                model_name=endpoint,
            )

    def start_training_job(
        self,
        job_name: str,
        training_data_s3_uri: str,
        output_s3_uri: str,
        hyperparameters: dict[str, str] | None = None,
        instance_type: str | None = None,
        instance_count: int = 1,
    ) -> str:
        """Start a SageMaker training job."""
        try:
            instance = instance_type or self.settings.training_instance_type

            training_params = {
                "TrainingJobName": job_name,
                "AlgorithmSpecification": {
                    "TrainingImage": self._get_training_image(),
                    "TrainingInputMode": "File",
                },
                "RoleArn": self._get_sagemaker_role_arn(),
                "InputDataConfig": [
                    {
                        "ChannelName": "training",
                        "DataSource": {
                            "S3DataSource": {
                                "S3DataType": "S3Prefix",
                                "S3Uri": training_data_s3_uri,
                                "S3DataDistributionType": "FullyReplicated",
                            }
                        },
                    }
                ],
                "OutputDataConfig": {"S3OutputPath": output_s3_uri},
                "ResourceConfig": {
                    "InstanceType": instance,
                    "InstanceCount": instance_count,
                    "VolumeSizeInGB": 50,
                },
                "StoppingCondition": {"MaxRuntimeInSeconds": 3600},
            }

            if hyperparameters:
                training_params["HyperParameters"] = hyperparameters

            self.clients.sagemaker.create_training_job(**training_params)

            logger.info(
                "Started training job",
                job_name=job_name,
                instance_type=instance,
            )
            return job_name

        except ClientError as e:
            raise NonRetryableError(f"Failed to start training job: {e}")

    def get_training_job_status(self, job_name: str) -> dict[str, Any]:
        """Get status of a training job."""
        response = self.clients.sagemaker.describe_training_job(
            TrainingJobName=job_name
        )

        return {
            "status": response.get("TrainingJobStatus"),
            "secondary_status": response.get("SecondaryStatus"),
            "failure_reason": response.get("FailureReason"),
            "model_artifacts": response.get("ModelArtifacts", {}).get("S3ModelArtifacts"),
            "training_time_seconds": response.get("TrainingTimeInSeconds"),
            "billable_time_seconds": response.get("BillableTimeInSeconds"),
        }

    def create_model(
        self,
        model_name: str,
        model_artifacts_s3_uri: str,
        image_uri: str | None = None,
    ) -> str:
        """Create a SageMaker model from training artifacts."""
        try:
            self.clients.sagemaker.create_model(
                ModelName=model_name,
                PrimaryContainer={
                    "Image": image_uri or self._get_inference_image(),
                    "ModelDataUrl": model_artifacts_s3_uri,
                },
                ExecutionRoleArn=self._get_sagemaker_role_arn(),
            )

            logger.info("Created model", model_name=model_name)
            return model_name

        except ClientError as e:
            raise NonRetryableError(f"Failed to create model: {e}")

    def create_endpoint_config(
        self,
        config_name: str,
        model_name: str,
        instance_type: str | None = None,
        instance_count: int = 1,
    ) -> str:
        """Create endpoint configuration."""
        try:
            instance = instance_type or self.settings.endpoint_instance_type

            self.clients.sagemaker.create_endpoint_config(
                EndpointConfigName=config_name,
                ProductionVariants=[
                    {
                        "VariantName": "primary",
                        "ModelName": model_name,
                        "InstanceType": instance,
                        "InitialInstanceCount": instance_count,
                    }
                ],
            )

            logger.info("Created endpoint config", config_name=config_name)
            return config_name

        except ClientError as e:
            raise NonRetryableError(f"Failed to create endpoint config: {e}")

    def update_endpoint(
        self,
        endpoint_name: str,
        new_config_name: str,
    ) -> None:
        """Update endpoint with new configuration (blue/green deployment)."""
        try:
            self.clients.sagemaker.update_endpoint(
                EndpointName=endpoint_name,
                EndpointConfigName=new_config_name,
            )

            logger.info(
                "Updating endpoint",
                endpoint_name=endpoint_name,
                config=new_config_name,
            )

        except ClientError as e:
            raise NonRetryableError(f"Failed to update endpoint: {e}")

    def register_model(
        self,
        model_package_group_name: str,
        model_artifacts_s3_uri: str,
        image_uri: str | None = None,
        model_metrics: dict[str, Any] | None = None,
    ) -> str:
        """Register model in Model Registry."""
        try:
            params: dict[str, Any] = {
                "ModelPackageGroupName": model_package_group_name,
                "InferenceSpecification": {
                    "Containers": [
                        {
                            "Image": image_uri or self._get_inference_image(),
                            "ModelDataUrl": model_artifacts_s3_uri,
                        }
                    ],
                    "SupportedContentTypes": ["application/json"],
                    "SupportedResponseMIMETypes": ["application/json"],
                },
                "ModelApprovalStatus": "PendingManualApproval",
            }

            if model_metrics:
                params["ModelMetrics"] = model_metrics

            response = self.clients.sagemaker.create_model_package(**params)
            model_package_arn = response["ModelPackageArn"]

            logger.info(
                "Registered model",
                model_package_arn=model_package_arn,
            )
            return model_package_arn

        except ClientError as e:
            raise NonRetryableError(f"Failed to register model: {e}")

    def _parse_inference_result(
        self,
        document_id: str,
        result: dict[str, Any],
        latency_ms: float,
    ) -> InferenceResult:
        """Parse inference response into InferenceResult."""
        # Handle different response formats
        if "predictions" in result:
            # Standard format
            predictions = result["predictions"]
            if isinstance(predictions, list) and predictions:
                pred = predictions[0]
                if isinstance(pred, dict):
                    return InferenceResult(
                        document_id=document_id,
                        predicted_class=pred.get("class", pred.get("label", "")),
                        confidence=pred.get("confidence", pred.get("score", 0)),
                        probabilities=pred.get("probabilities", {}),
                        latency_ms=latency_ms,
                    )

        # Simple classification format
        if "class" in result:
            return InferenceResult(
                document_id=document_id,
                predicted_class=result["class"],
                confidence=result.get("confidence", result.get("score", 0)),
                probabilities=result.get("probabilities", {}),
                latency_ms=latency_ms,
            )

        # Return raw result as class
        return InferenceResult(
            document_id=document_id,
            predicted_class=str(result),
            confidence=0.0,
            latency_ms=latency_ms,
        )

    def _get_training_image(self) -> str:
        """Get training container image URI."""
        # This would typically come from configuration
        # Using XGBoost as default example
        region = self.settings.aws_region
        return f"683313688378.dkr.ecr.{region}.amazonaws.com/sagemaker-xgboost:1.7-1"

    def _get_inference_image(self) -> str:
        """Get inference container image URI."""
        region = self.settings.aws_region
        return f"683313688378.dkr.ecr.{region}.amazonaws.com/sagemaker-xgboost:1.7-1"

    def _get_sagemaker_role_arn(self) -> str:
        """Get SageMaker execution role ARN."""
        # This should come from configuration/Terraform
        # Placeholder - should be set via environment variable
        import os

        return os.environ.get("SAGEMAKER_ROLE_ARN", "")
