"""Lake Formation service for data governance and security."""

from typing import Any

import boto3

from ..common.config import settings
from ..common.exceptions import DataLocationError, LakeFormationError, PermissionDeniedError
from ..common.models import LakeFormationPermission, PermissionType


class LakeFormationService:
    """Service for AWS Lake Formation operations.

    Lake Formation provides centralized governance for data lakes with:
    - Fine-grained access control at database, table, and column level
    - Data location registration for S3 paths
    - Tag-based access control (LF-Tags)
    - Integration with AWS Glue Data Catalog

    IMPORTANT: Principals need BOTH:
    1. Lake Formation permissions (granted via this service)
    2. IAM permission: lakeformation:GetDataAccess
    """

    def __init__(self) -> None:
        """Initialize the Lake Formation service."""
        self.client = boto3.client("lakeformation", region_name=settings.aws_region)
        self.database = settings.glue_database

    def register_data_location(
        self,
        s3_location: str,
        role_arn: str,
        use_service_linked_role: bool = False,
    ) -> None:
        """Register an S3 location with Lake Formation.

        This is required before Lake Formation can manage access to data
        stored in this location. The role must have permissions to access
        the S3 location.

        Args:
            s3_location: S3 URI (e.g., s3://bucket/prefix/)
            role_arn: IAM role ARN for accessing the location
            use_service_linked_role: Use service-linked role instead

        Raises:
            DataLocationError: If registration fails
        """
        try:
            resource_info: dict[str, Any] = {"ResourceArn": s3_location}

            if use_service_linked_role:
                resource_info["UseServiceLinkedRole"] = True
            else:
                resource_info["RoleArn"] = role_arn

            self.client.register_resource(**resource_info)
        except self.client.exceptions.AlreadyExistsException:
            pass
        except Exception as e:
            raise DataLocationError(s3_location, str(e))

    def deregister_data_location(self, s3_location: str) -> None:
        """Deregister an S3 location from Lake Formation.

        Args:
            s3_location: S3 URI to deregister
        """
        self.client.deregister_resource(ResourceArn=s3_location)

    def grant_database_permissions(
        self,
        principal_arn: str,
        database: str | None = None,
        permissions: list[PermissionType] | None = None,
        grant_option: bool = False,
    ) -> None:
        """Grant database-level permissions.

        Args:
            principal_arn: IAM principal ARN (user, role, or group)
            database: Database name (defaults to config)
            permissions: Permissions to grant (defaults to DESCRIBE)
            grant_option: Allow principal to grant these permissions to others
        """
        db_name = database or self.database
        perms = permissions or [PermissionType.DESCRIBE]

        perm_strings = [p.value for p in perms]
        grant_perms = perm_strings if grant_option else []

        self.client.grant_permissions(
            Principal={"DataLakePrincipalIdentifier": principal_arn},
            Resource={"Database": {"Name": db_name}},
            Permissions=perm_strings,
            PermissionsWithGrantOption=grant_perms,
        )

    def grant_table_permissions(
        self,
        principal_arn: str,
        table_name: str,
        database: str | None = None,
        permissions: list[PermissionType] | None = None,
        column_names: list[str] | None = None,
        grant_option: bool = False,
    ) -> None:
        """Grant table-level permissions.

        Args:
            principal_arn: IAM principal ARN
            table_name: Table name
            database: Database name (defaults to config)
            permissions: Permissions to grant (defaults to SELECT)
            column_names: Specific columns (for column-level security)
            grant_option: Allow principal to grant permissions
        """
        db_name = database or self.database
        perms = permissions or [PermissionType.SELECT]
        perm_strings = [p.value for p in perms]
        grant_perms = perm_strings if grant_option else []

        if column_names:
            resource = {
                "TableWithColumns": {
                    "DatabaseName": db_name,
                    "Name": table_name,
                    "ColumnNames": column_names,
                }
            }
        else:
            resource = {
                "Table": {
                    "DatabaseName": db_name,
                    "Name": table_name,
                }
            }

        self.client.grant_permissions(
            Principal={"DataLakePrincipalIdentifier": principal_arn},
            Resource=resource,
            Permissions=perm_strings,
            PermissionsWithGrantOption=grant_perms,
        )

    def grant_data_location_permission(
        self,
        principal_arn: str,
        s3_location: str,
        grant_option: bool = False,
    ) -> None:
        """Grant data location access permission.

        This allows the principal to create tables pointing to this S3 location.
        The principal must also have lakeformation:GetDataAccess IAM permission.

        Args:
            principal_arn: IAM principal ARN
            s3_location: S3 URI
            grant_option: Allow principal to grant permissions
        """
        perms = [PermissionType.DATA_LOCATION_ACCESS.value]
        grant_perms = perms if grant_option else []

        self.client.grant_permissions(
            Principal={"DataLakePrincipalIdentifier": principal_arn},
            Resource={"DataLocation": {"ResourceArn": s3_location}},
            Permissions=perms,
            PermissionsWithGrantOption=grant_perms,
        )

    def revoke_permissions(
        self,
        principal_arn: str,
        resource: dict[str, Any],
        permissions: list[PermissionType],
    ) -> None:
        """Revoke permissions from a principal.

        Args:
            principal_arn: IAM principal ARN
            resource: Lake Formation resource specification
            permissions: Permissions to revoke
        """
        self.client.revoke_permissions(
            Principal={"DataLakePrincipalIdentifier": principal_arn},
            Resource=resource,
            Permissions=[p.value for p in permissions],
        )

    def list_permissions(
        self,
        principal_arn: str | None = None,
        resource_type: str | None = None,
    ) -> list[LakeFormationPermission]:
        """List Lake Formation permissions.

        Args:
            principal_arn: Filter by principal
            resource_type: Filter by resource type (DATABASE, TABLE, etc.)

        Returns:
            List of permission grants
        """
        params: dict[str, Any] = {}

        if principal_arn:
            params["Principal"] = {"DataLakePrincipalIdentifier": principal_arn}

        if resource_type:
            params["ResourceType"] = resource_type

        results = []
        paginator = self.client.get_paginator("list_permissions")

        for page in paginator.paginate(**params):
            for entry in page.get("PrincipalResourcePermissions", []):
                principal = entry["Principal"]["DataLakePrincipalIdentifier"]
                resource = entry["Resource"]
                perms = entry.get("Permissions", [])
                grant_perms = entry.get("PermissionsWithGrantOption", [])

                # Determine resource type and ARN
                if "Database" in resource:
                    res_type = "DATABASE"
                    res_arn = resource["Database"]["Name"]
                elif "Table" in resource:
                    res_type = "TABLE"
                    db = resource["Table"]["DatabaseName"]
                    tbl = resource["Table"]["Name"]
                    res_arn = f"{db}.{tbl}"
                elif "TableWithColumns" in resource:
                    res_type = "COLUMN"
                    db = resource["TableWithColumns"]["DatabaseName"]
                    tbl = resource["TableWithColumns"]["Name"]
                    res_arn = f"{db}.{tbl}"
                elif "DataLocation" in resource:
                    res_type = "DATA_LOCATION"
                    res_arn = resource["DataLocation"]["ResourceArn"]
                else:
                    continue

                results.append(
                    LakeFormationPermission(
                        principal=principal,
                        resource_type=res_type,
                        resource_arn=res_arn,
                        permissions=[PermissionType(p) for p in perms],
                        permissions_with_grant_option=[
                            PermissionType(p) for p in grant_perms
                        ],
                    )
                )

        return results

    def set_data_lake_settings(
        self,
        admin_arns: list[str],
        create_database_default_permissions: bool = False,
        create_table_default_permissions: bool = False,
    ) -> None:
        """Configure data lake settings.

        Args:
            admin_arns: List of IAM ARNs for data lake administrators
            create_database_default_permissions: Allow default CREATE_DATABASE
            create_table_default_permissions: Allow default CREATE_TABLE

        Note:
            For Lake Formation to manage permissions (instead of IAM),
            disable default permissions by setting both flags to False.
        """
        admins = [{"DataLakePrincipalIdentifier": arn} for arn in admin_arns]

        settings_config: dict[str, Any] = {"DataLakeAdmins": admins}

        if not create_database_default_permissions:
            settings_config["CreateDatabaseDefaultPermissions"] = []

        if not create_table_default_permissions:
            settings_config["CreateTableDefaultPermissions"] = []

        self.client.put_data_lake_settings(DataLakeSettings=settings_config)

    def get_data_lake_settings(self) -> dict[str, Any]:
        """Get current data lake settings.

        Returns:
            Data lake settings including admins and default permissions
        """
        response = self.client.get_data_lake_settings()
        return response.get("DataLakeSettings", {})

    def check_permission(
        self,
        principal_arn: str,
        table_name: str,
        permission: PermissionType,
        database: str | None = None,
    ) -> bool:
        """Check if principal has permission on a table.

        Args:
            principal_arn: IAM principal ARN
            table_name: Table name
            permission: Permission to check
            database: Database name

        Returns:
            True if permission is granted
        """
        permissions = self.list_permissions(principal_arn=principal_arn)

        for perm in permissions:
            if perm.resource_type in ("TABLE", "COLUMN"):
                db_table = f"{database or self.database}.{table_name}"
                if perm.resource_arn == db_table and permission in perm.permissions:
                    return True

        return False

    def create_lf_tag(self, tag_key: str, tag_values: list[str]) -> None:
        """Create a Lake Formation tag for tag-based access control.

        Args:
            tag_key: Tag key name
            tag_values: Allowed tag values
        """
        self.client.create_lf_tag(TagKey=tag_key, TagValues=tag_values)

    def assign_lf_tag_to_table(
        self,
        table_name: str,
        tag_key: str,
        tag_values: list[str],
        database: str | None = None,
    ) -> None:
        """Assign LF-Tag to a table.

        Args:
            table_name: Table name
            tag_key: Tag key
            tag_values: Tag values to assign
            database: Database name
        """
        self.client.add_lf_tags_to_resource(
            Resource={
                "Table": {
                    "DatabaseName": database or self.database,
                    "Name": table_name,
                }
            },
            LFTags=[{"TagKey": tag_key, "TagValues": tag_values}],
        )
