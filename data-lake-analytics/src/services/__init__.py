"""Services for AWS Athena data lake analytics."""

from .athena_service import AthenaService
from .glue_service import GlueService
from .lakeformation_service import LakeFormationService
from .s3_service import S3Service

__all__ = [
    "AthenaService",
    "GlueService",
    "LakeFormationService",
    "S3Service",
]


def get_athena_service() -> AthenaService:
    """Get Athena service instance."""
    return AthenaService()


def get_glue_service() -> GlueService:
    """Get Glue service instance."""
    return GlueService()


def get_lakeformation_service() -> LakeFormationService:
    """Get Lake Formation service instance."""
    return LakeFormationService()


def get_s3_service() -> S3Service:
    """Get S3 service instance."""
    return S3Service()
