import asyncio
import httpx
import time
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError

app = FastAPI()
security = HTTPBearer()

# KEYCLOAK_BASE = "http://localhost:8080"
KEYCLOAK_BASE = "http://keycloak:8080"
REALM = "demo-realm"
CLIENT_ID = "vue-client"

# cached config / jwks
openid_config = {}
jwks = {}
jwks_last_refresh = 0

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8081",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------
# 🔹 Helper functions
# -----------------------------------------------

async def fetch_openid_config():
    """Fetch OpenID configuration dynamically from Keycloak."""
    global openid_config
    url = f"{KEYCLOAK_BASE}/realms/{REALM}/.well-known/openid-configuration"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, timeout=10)
            r.raise_for_status()
            openid_config = r.json()
            print("✅ OpenID configuration fetched successfully.")
            return openid_config   
    except Exception as e:
        print(f"⚠️ Could not fetch OpenID config: {e}")
        openid_config = {}
        return openid_config 

async def fetch_jwks():
    """Fetch JWKS keys from Keycloak."""
    global jwks, jwks_last_refresh

    if not openid_config.get("jwks_uri"):
        await fetch_openid_config()
    jwks_uri = openid_config.get("jwks_uri")

    if not jwks_uri:
        print("⚠️ JWKS URI not found yet, skipping fetch_jwks()")
        return

    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(jwks_uri, timeout=10)
            r.raise_for_status()
            jwks = r.json()
            jwks_last_refresh = time.time()
            print("✅ JWKS keys fetched successfully.")
    except Exception as e:
        print(f"⚠️ Could not fetch JWKS: {e}")

@app.on_event("startup")
async def startup_event():
    # 🟢 Don't block startup — just schedule background fetch
    asyncio.create_task(fetch_openid_config())
    asyncio.create_task(fetch_jwks())
    print("🚀 Backend started without waiting for Keycloak.")

def get_kid_and_key(token):
    headers = jwt.get_unverified_headers(token)
    kid = headers.get("kid")
    for key in jwks.get("keys", []):
        if key["kid"] == kid:
            return key
    return None

# -----------------------------------------------
# 🔒 Authentication dependency (auto-retry JWKS)
# -----------------------------------------------
async def verify_token_and_role(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    global jwks, openid_config

    # 🧠 Ensure OpenID config and JWKS are loaded
    if not openid_config:
        print("⚙️ OpenID config empty — refetching...")
        try:
            openid_config = await fetch_openid_config()
            print("✅ OpenID config fetched.")
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Cannot fetch OpenID config: {str(e)}")

    if not jwks or time.time() - jwks_last_refresh > 3600:
        print("🔁 Refreshing JWKS...")
        try:
            await fetch_jwks()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Cannot fetch JWKS: {str(e)}")

    # 🔑 Verify key ID (kid)
    key = get_kid_and_key(token)
    print("🔍 Token kid:", jwt.get_unverified_headers(token).get("kid"))
    print("🔍 Found key kid:", key.get("kid") if key else "None")

    if not key:
        # 💡 Retry one more time if JWKS was stale
        print("⚠️ Kid not found, retrying JWKS fetch...")
        await fetch_jwks()
        key = get_kid_and_key(token)
        if not key:
            raise HTTPException(status_code=401, detail="Unknown or missing key ID (kid)")

    try:
        claims = jwt.decode(
            token,
            key,
            algorithms=[key.get("alg", "RS256")],
            audience=None,
            options={"verify_aud": False},
        )
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    # ✅ Verify issuer matches (we can make this more lenient too)
    issuer = openid_config.get("issuer")
    token_issuer = claims.get("iss")
    print(f"🔍 OpenID config issuer: {issuer}")
    print(f"🔍 Token issuer: {token_issuer}")

    valid_issuers = [
    issuer,
    "http://localhost:8080/realms/demo-realm"
]

    if token_issuer not in valid_issuers:
        raise HTTPException(status_code=401, detail=f"Invalid issuer: {token_issuer}")


    # ✅ Role check
    realm_access = claims.get("realm_access", {})
    roles = realm_access.get("roles", [])
    if "dashboard" not in roles:
        raise HTTPException(status_code=403, detail="Insufficient role")

    return {
        "sub": claims.get("sub"),
        "preferred_username": claims.get("preferred_username"),
        "roles": roles,
    }


# -----------------------------------------------
# 🧭 Routes
# -----------------------------------------------
@app.get("/dashboard")
async def dashboard(user=Depends(verify_token_and_role)):
    return {
        "message": f"Hello {user['preferred_username']}, welcome to the protected dashboard!",
        "meta": {"widgets": 3, "time": time.time()}
    }

@app.get("/")
async def root():
    return {"ok": True, "realm": REALM}
