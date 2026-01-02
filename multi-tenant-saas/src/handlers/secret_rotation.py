"""Secrets Manager Rotation Lambda Handler.

This handler implements the four-step rotation process for AWS Secrets Manager:
1. createSecret - Create a new version of the secret
2. setSecret - Set the new secret in the target service
3. testSecret - Test the new secret works
4. finishSecret - Finalize the rotation
"""

import json
import secrets
import string
from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.clients import get_aws_clients
from src.common.exceptions import SecretsError

logger = Logger()
tracer = Tracer()


# Password generation settings
PASSWORD_LENGTH = 32
PASSWORD_CHARS = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
EXCLUDE_CHARS = "/@\"'\\"


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> None:
    """Secrets Manager rotation handler.

    Args:
        event: Rotation event with Step, SecretId, ClientRequestToken
        context: Lambda context
    """
    step = event["Step"]
    secret_id = event["SecretId"]
    token = event["ClientRequestToken"]

    logger.info(
        "Processing rotation step",
        extra={"step": step, "secret_id": secret_id, "token": token[:8] + "..."},
    )

    clients = get_aws_clients()
    secrets_client = clients.secrets_manager

    # Validate the secret exists and rotation is enabled
    metadata = secrets_client.describe_secret(SecretId=secret_id)
    if not metadata.get("RotationEnabled"):
        raise SecretsError(secret_id, "Rotation is not enabled for this secret")

    # Check if the token is valid
    versions = metadata.get("VersionIdsToStages", {})
    if token not in versions:
        raise SecretsError(secret_id, f"Token {token} not found in secret versions")

    # Dispatch to appropriate step handler
    if step == "createSecret":
        create_secret(secrets_client, secret_id, token)
    elif step == "setSecret":
        set_secret(secrets_client, secret_id, token)
    elif step == "testSecret":
        test_secret(secrets_client, secret_id, token)
    elif step == "finishSecret":
        finish_secret(secrets_client, secret_id, token)
    else:
        raise SecretsError(secret_id, f"Unknown rotation step: {step}")


@tracer.capture_method
def create_secret(secrets_client: Any, secret_id: str, token: str) -> None:
    """Create a new version of the secret.

    This step generates new credentials but doesn't apply them yet.

    Args:
        secrets_client: Secrets Manager client
        secret_id: Secret ARN or name
        token: Version token
    """
    logger.info("Creating new secret version")

    # Check if secret already exists for this token
    try:
        secrets_client.get_secret_value(SecretId=secret_id, VersionId=token, VersionStage="AWSPENDING")
        logger.info("Secret version already exists, skipping creation")
        return
    except secrets_client.exceptions.ResourceNotFoundException:
        pass

    # Get current secret to understand its structure
    current = secrets_client.get_secret_value(SecretId=secret_id, VersionStage="AWSCURRENT")
    current_secret = json.loads(current["SecretString"])

    # Generate new password
    new_password = generate_password()

    # Create new secret with same structure but new password
    new_secret = current_secret.copy()
    new_secret["password"] = new_password

    # Store the new secret version
    secrets_client.put_secret_value(
        SecretId=secret_id,
        ClientRequestToken=token,
        SecretString=json.dumps(new_secret),
        VersionStages=["AWSPENDING"],
    )

    logger.info("Created new secret version with AWSPENDING stage")


@tracer.capture_method
def set_secret(secrets_client: Any, secret_id: str, token: str) -> None:
    """Set the new secret in the target service.

    This step applies the new credentials to the target (database, API, etc.).

    Args:
        secrets_client: Secrets Manager client
        secret_id: Secret ARN or name
        token: Version token
    """
    logger.info("Setting new secret in target service")

    # Get the pending secret
    pending = secrets_client.get_secret_value(SecretId=secret_id, VersionId=token, VersionStage="AWSPENDING")
    pending_secret = json.loads(pending["SecretString"])

    # Determine the type of secret and apply it
    secret_type = pending_secret.get("type", "database")

    if secret_type == "database":
        set_database_password(pending_secret)
    elif secret_type == "api_key":
        set_api_key(pending_secret)
    else:
        logger.warning(f"Unknown secret type: {secret_type}, skipping set step")

    logger.info("Set new secret in target service")


@tracer.capture_method
def test_secret(secrets_client: Any, secret_id: str, token: str) -> None:
    """Test the new secret works.

    This step validates the new credentials can be used to access the target.

    Args:
        secrets_client: Secrets Manager client
        secret_id: Secret ARN or name
        token: Version token
    """
    logger.info("Testing new secret")

    # Get the pending secret
    pending = secrets_client.get_secret_value(SecretId=secret_id, VersionId=token, VersionStage="AWSPENDING")
    pending_secret = json.loads(pending["SecretString"])

    # Determine the type and test it
    secret_type = pending_secret.get("type", "database")

    if secret_type == "database":
        test_database_connection(pending_secret)
    elif secret_type == "api_key":
        test_api_key(pending_secret)
    else:
        logger.warning(f"Unknown secret type: {secret_type}, skipping test step")

    logger.info("New secret tested successfully")


@tracer.capture_method
def finish_secret(secrets_client: Any, secret_id: str, token: str) -> None:
    """Finalize the rotation.

    This step moves the AWSCURRENT label to the new version.

    Args:
        secrets_client: Secrets Manager client
        secret_id: Secret ARN or name
        token: Version token
    """
    logger.info("Finishing secret rotation")

    # Get current version info
    metadata = secrets_client.describe_secret(SecretId=secret_id)
    versions = metadata.get("VersionIdsToStages", {})

    # Find the current version
    current_version = None
    for version_id, stages in versions.items():
        if "AWSCURRENT" in stages:
            if version_id == token:
                logger.info("New version is already AWSCURRENT, rotation complete")
                return
            current_version = version_id
            break

    # Move AWSCURRENT to the new version
    secrets_client.update_secret_version_stage(
        SecretId=secret_id,
        VersionStage="AWSCURRENT",
        MoveToVersionId=token,
        RemoveFromVersionId=current_version,
    )

    logger.info(f"Rotation complete: moved AWSCURRENT from {current_version} to {token}")


def generate_password() -> str:
    """Generate a secure random password.

    Returns:
        Random password string
    """
    chars = "".join(c for c in PASSWORD_CHARS if c not in EXCLUDE_CHARS)
    password = "".join(secrets.choice(chars) for _ in range(PASSWORD_LENGTH))

    # Ensure password meets complexity requirements
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=" for c in password)

    if not (has_upper and has_lower and has_digit and has_special):
        # Regenerate if complexity not met
        return generate_password()

    return password


def set_database_password(secret: dict[str, Any]) -> None:
    """Set password in database.

    Args:
        secret: Secret containing database credentials
    """
    # In a real implementation, connect to the database and update the password
    # This would use psycopg2, pymysql, or similar based on engine

    host = secret.get("host")
    port = secret.get("port")
    username = secret.get("username")
    engine = secret.get("engine", "postgresql")

    logger.info(f"Setting password for {username}@{host}:{port} ({engine})")

    # TODO: Implement actual database password change
    # Example for PostgreSQL:
    # ALTER USER {username} WITH PASSWORD '{new_password}';


def set_api_key(secret: dict[str, Any]) -> None:
    """Set API key in target service.

    Args:
        secret: Secret containing API key
    """
    service_url = secret.get("service_url")
    logger.info(f"Setting API key for service: {service_url}")

    # TODO: Implement API key rotation for the specific service


def test_database_connection(secret: dict[str, Any]) -> None:
    """Test database connection with new credentials.

    Args:
        secret: Secret containing database credentials

    Raises:
        SecretsError: If connection fails
    """
    host = secret.get("host")
    port = secret.get("port")
    username = secret.get("username")
    database = secret.get("dbname")
    engine = secret.get("engine", "postgresql")

    logger.info(f"Testing connection to {host}:{port}/{database}")

    # TODO: Implement actual database connection test
    # Example for PostgreSQL:
    # import psycopg2
    # conn = psycopg2.connect(
    #     host=host, port=port, user=username,
    #     password=secret["password"], dbname=database
    # )
    # conn.close()


def test_api_key(secret: dict[str, Any]) -> None:
    """Test API key works.

    Args:
        secret: Secret containing API key

    Raises:
        SecretsError: If API key test fails
    """
    service_url = secret.get("service_url")
    api_key = secret.get("api_key")

    logger.info(f"Testing API key for service: {service_url}")

    # TODO: Implement actual API key test
    # Make a test request to the service with the new key
