"""Security utilities for JWT validation and authorization."""

import json
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import httpx
from jose import JWTError, jwk, jwt
from jose.utils import base64url_decode

from src.common.config import get_settings
from src.common.exceptions import AuthenticationError, AuthorizationError
from src.common.models import TenantContext, TenantTier


@dataclass
class JWKSKey:
    """JSON Web Key Set key."""

    kid: str
    alg: str
    kty: str
    e: str
    n: str
    use: str


class JWTValidator:
    """JWT token validator for Cognito tokens."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._jwks_keys: dict[str, JWKSKey] | None = None
        self._jwks_last_fetch: float = 0
        self._jwks_cache_duration: int = 3600  # 1 hour

    def _fetch_jwks(self) -> dict[str, JWKSKey]:
        """Fetch JWKS from Cognito."""
        if (
            self._jwks_keys is not None
            and time.time() - self._jwks_last_fetch < self._jwks_cache_duration
        ):
            return self._jwks_keys

        try:
            response = httpx.get(self._settings.cognito_jwks_url, timeout=5.0)
            response.raise_for_status()
            jwks_data = response.json()

            self._jwks_keys = {}
            for key in jwks_data.get("keys", []):
                self._jwks_keys[key["kid"]] = JWKSKey(
                    kid=key["kid"],
                    alg=key["alg"],
                    kty=key["kty"],
                    e=key["e"],
                    n=key["n"],
                    use=key["use"],
                )
            self._jwks_last_fetch = time.time()
            return self._jwks_keys

        except Exception as e:
            raise AuthenticationError(f"Failed to fetch JWKS: {e}") from e

    def _get_public_key(self, token: str) -> Any:
        """Get the public key for a token."""
        try:
            headers = jwt.get_unverified_headers(token)
            kid = headers.get("kid")

            if not kid:
                raise AuthenticationError("Token missing key ID")

            jwks = self._fetch_jwks()
            if kid not in jwks:
                # Refresh JWKS in case of key rotation
                self._jwks_keys = None
                jwks = self._fetch_jwks()

                if kid not in jwks:
                    raise AuthenticationError("Unknown key ID in token")

            key_data = jwks[kid]
            return jwk.construct(
                {
                    "kty": key_data.kty,
                    "e": key_data.e,
                    "n": key_data.n,
                    "alg": key_data.alg,
                    "use": key_data.use,
                }
            )

        except JWTError as e:
            raise AuthenticationError(f"Invalid token headers: {e}") from e

    def validate_token(self, token: str) -> dict[str, Any]:
        """Validate a JWT token and return claims.

        Args:
            token: The JWT token to validate

        Returns:
            Dictionary of token claims

        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            # Get the public key
            public_key = self._get_public_key(token)

            # Decode and validate the token
            claims = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=self._settings.cognito_client_id,
                issuer=self._settings.cognito_issuer,
                options={
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True,
                },
            )

            return claims

        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.JWTClaimsError as e:
            raise AuthenticationError(f"Invalid token claims: {e}")
        except JWTError as e:
            raise AuthenticationError(f"Invalid token: {e}")

    def extract_tenant_context(self, claims: dict[str, Any]) -> TenantContext:
        """Extract tenant context from JWT claims.

        Args:
            claims: Validated JWT claims

        Returns:
            TenantContext with user and tenant information

        Raises:
            AuthenticationError: If required claims are missing
        """
        tenant_id = claims.get("custom:tenant_id")
        if not tenant_id:
            raise AuthenticationError("Token missing tenant_id claim")

        user_id = claims.get("sub")
        if not user_id:
            raise AuthenticationError("Token missing sub claim")

        # Parse roles from Cognito groups
        roles = claims.get("cognito:groups", [])
        if isinstance(roles, str):
            roles = [roles]

        # Parse tier from custom claim
        tier_str = claims.get("custom:tier", "free")
        try:
            tier = TenantTier(tier_str.lower())
        except ValueError:
            tier = TenantTier.FREE

        return TenantContext(
            tenant_id=tenant_id,
            user_id=user_id,
            email=claims.get("email"),
            roles=roles,
            permissions=self._roles_to_permissions(roles),
            tier=tier,
            metadata={
                "token_use": claims.get("token_use"),
                "auth_time": claims.get("auth_time"),
                "iat": claims.get("iat"),
                "exp": claims.get("exp"),
            },
        )

    def _roles_to_permissions(self, roles: list[str]) -> list[str]:
        """Convert roles to permissions."""
        permission_map = {
            "admin": ["read", "write", "delete", "admin"],
            "editor": ["read", "write"],
            "viewer": ["read"],
        }

        permissions = set()
        for role in roles:
            role_lower = role.lower()
            if role_lower in permission_map:
                permissions.update(permission_map[role_lower])

        return list(permissions)


class Authorizer:
    """Authorization helper for permission checks."""

    def __init__(self, context: TenantContext) -> None:
        self.context = context

    def require_permission(self, permission: str) -> None:
        """Require a specific permission.

        Args:
            permission: The permission required

        Raises:
            AuthorizationError: If permission is not granted
        """
        if permission not in self.context.permissions:
            raise AuthorizationError(
                message=f"Permission '{permission}' required",
                required_permission=permission,
            )

    def require_any_permission(self, permissions: list[str]) -> None:
        """Require any of the specified permissions.

        Args:
            permissions: List of acceptable permissions

        Raises:
            AuthorizationError: If none of the permissions are granted
        """
        if not any(p in self.context.permissions for p in permissions):
            raise AuthorizationError(
                message=f"One of these permissions required: {permissions}",
                required_permission=", ".join(permissions),
            )

    def require_role(self, role: str) -> None:
        """Require a specific role.

        Args:
            role: The role required

        Raises:
            AuthorizationError: If role is not assigned
        """
        if role not in self.context.roles:
            raise AuthorizationError(
                message=f"Role '{role}' required",
                required_permission=f"role:{role}",
            )

    def require_tier(self, minimum_tier: TenantTier) -> None:
        """Require a minimum subscription tier.

        Args:
            minimum_tier: The minimum tier required

        Raises:
            AuthorizationError: If tenant tier is lower than required
        """
        tier_order = [TenantTier.FREE, TenantTier.BASIC, TenantTier.PROFESSIONAL, TenantTier.ENTERPRISE]
        current_index = tier_order.index(self.context.tier)
        required_index = tier_order.index(minimum_tier)

        if current_index < required_index:
            raise AuthorizationError(
                message=f"Subscription tier '{minimum_tier.value}' or higher required",
                required_permission=f"tier:{minimum_tier.value}",
            )

    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return "admin" in [r.lower() for r in self.context.roles]

    def can_access_tenant(self, tenant_id: str) -> bool:
        """Check if user can access a specific tenant's resources.

        Args:
            tenant_id: The tenant ID to check

        Returns:
            True if access is allowed
        """
        # Users can only access their own tenant unless they're super admin
        if "super_admin" in self.context.roles:
            return True
        return self.context.tenant_id == tenant_id


def generate_policy(
    principal_id: str,
    effect: str,
    resource: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate an IAM policy document for API Gateway authorizer.

    Args:
        principal_id: The principal (user) ID
        effect: Allow or Deny
        resource: The API Gateway resource ARN
        context: Additional context to pass to the handler

    Returns:
        Policy document dictionary
    """
    policy = {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": resource,
                }
            ],
        },
    }

    if context:
        # Flatten context values to strings (API Gateway requirement)
        policy["context"] = {
            k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
            for k, v in context.items()
        }

    return policy


@lru_cache
def get_jwt_validator() -> JWTValidator:
    """Get cached JWT validator instance."""
    return JWTValidator()
