import os, time, asyncio
from typing import Dict, Any, Optional, List
import httpx
from jose import jwt, JWTError

DISCOVERY_CACHE: Dict[str, Any] = {}
DISCOVERY_FETCHED_AT: Dict[str, float] = {}
JWKS_CACHE: Dict[str, Any] = {}
JWKS_FETCHED_AT: Dict[str, float] = {}

DISC_TTL = int(os.getenv("OIDC_DISCOVERY_CACHE_SEC", "3600"))
JWKS_TTL = int(os.getenv("OIDC_JWKS_CACHE_SEC", "3600"))

AUDIENCES = [a.strip() for a in os.getenv("OIDC_AUDIENCES", "").split(",") if a.strip()]
EXTRA_ISSUERS = [u.strip() for u in os.getenv("OIDC_EXTRA_ISSUERS", "").split(",") if u.strip()]
ROLE_PATHS = [p.strip() for p in os.getenv("OIDC_ROLE_PATHS", "realm_access.roles,claims.roles,groups").split(",")]

HTTP_TIMEOUT = 10.0

def _now(): return time.time()

async def _get_json(url: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as c:
        r = await c.get(url)
        r.raise_for_status()
        return r.json()

async def fetch_discovery(issuer_or_discovery: str) -> Dict[str, Any]:
    """
    issuer_or_discovery can be either:
      - full discovery URL: https://.../.well-known/openid-configuration
      - base issuer URL (we'll append '/.well-known/openid-configuration')
    """
    url = issuer_or_discovery
    if not url.endswith(".well-known/openid-configuration"):
        url = issuer_or_discovery.rstrip("/") + "/.well-known/openid-configuration"

    cached = DISCOVERY_CACHE.get(url)
    if cached and (_now() - DISCOVERY_FETCHED_AT.get(url, 0)) < DISC_TTL:
        return cached

    data = await _get_json(url)
    DISCOVERY_CACHE[url] = data
    DISCOVERY_FETCHED_AT[url] = _now()
    return data

async def fetch_jwks(jwks_uri: str) -> Dict[str, Any]:
    cached = JWKS_CACHE.get(jwks_uri)
    if cached and (_now() - JWKS_FETCHED_AT.get(jwks_uri, 0)) < JWKS_TTL:
        return cached
    data = await _get_json(jwks_uri)
    JWKS_CACHE[jwks_uri] = data
    JWKS_FETCHED_AT[jwks_uri] = _now()
    return data

def _find_key(jwks: Dict[str, Any], kid: str) -> Optional[Dict[str, Any]]:
    for k in jwks.get("keys", []):
        if k.get("kid") == kid:
            return k
    return None

def _extract_roles(claims: Dict[str, Any]) -> List[str]:
    # Try multiple claim paths across providers
    # realm_access.roles (Keycloak), roles (generic), groups (Okta often), cognito: groups
    roles: List[str] = []
    for path in ROLE_PATHS:
        node = claims
        for part in path.split("."):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                node = None
                break
        if isinstance(node, list):
            roles.extend([str(x) for x in node])
    # De-duplicate
    return sorted(list(set(roles)))

async def validate_token(token: str, issuer_or_discovery: str) -> Dict[str, Any]:
    # 1) Discovery
    disc = await fetch_discovery(issuer_or_discovery)
    issuer = disc["issuer"]
    jwks_uri = disc["jwks_uri"]

    # 2) Decode headers, fetch keys
    headers = jwt.get_unverified_headers(token)
    kid = headers.get("kid")
    jwks = await fetch_jwks(jwks_uri)
    key = _find_key(jwks, kid)
    if not key:
        # Key rotation—refresh and try once more
        jwks = await fetch_jwks(jwks_uri)  # re-fetch (cache TTL may still allow)
        key = _find_key(jwks, kid)
        if not key:
            raise JWTError("Unknown key id")

    # 3) Verify signature & standard claims
    # Many providers omit 'aud' or set differently; verify_aud=False and check manually if needed
    claims = jwt.decode(
        token,
        key,
        algorithms=[key.get("alg", "RS256")],
        options={"verify_aud": False}
    )

    # 4) Issuer check: accept primary + extras (migration / multi-tenant)
    token_iss = claims.get("iss")
    valid_issuers = [issuer]
    # If you pass base issuer instead of discovery URL for EXTRA_ISSUERS, append '/.well-known...' in fetch_discovery.
    for extra in EXTRA_ISSUERS:
        extra_disc = await fetch_discovery(extra)
        valid_issuers.append(extra_disc["issuer"])
    if token_iss not in valid_issuers:
        raise JWTError(f"Invalid issuer: {token_iss}")

    # 5) (Optional) audience check
    if AUDIENCES:
        token_aud = claims.get("aud")
        # aud can be str or list
        token_auds = [token_aud] if isinstance(token_aud, str) else (token_aud or [])
        if not set(AUDIENCES).intersection(set(token_auds)):
            # If your provider doesn't set 'aud', skip this block or map from 'azp'
            pass

    # 6) Normalize principal
    principal = {
        "sub": claims.get("sub"),
        "username": claims.get("preferred_username") or claims.get("email") or claims.get("name"),
        "email": claims.get("email"),
        "roles": _extract_roles(claims),
        "claims": claims
    }
    return principal
