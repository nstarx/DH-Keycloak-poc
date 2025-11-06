import os
import time
import asyncio
import httpx
from fastapi import FastAPI, Depends, Request, HTTPException, Response
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt
from urllib.parse import urlencode

# -----------------------------------------------------------
# ✅ CONFIGURATION
# -----------------------------------------------------------

CLIENT_ID = os.getenv("OIDC_CLIENT_ID", "vue-client")
CLIENT_SECRET = os.getenv("OIDC_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("BFF_REDIRECT_URI", "http://localhost:8000/auth/callback")

# These are the possible Keycloak URLs your backend may see
POSSIBLE_ISSUERS = [
    "http://keycloak:8080/realms/demo-realm",
    "http://host.docker.internal:8080/realms/demo-realm",
    "http://localhost:8080/realms/demo-realm",
]

SCOPES = "openid email profile offline_access"

COOKIE_ACCESS = "bff_at"
COOKIE_REFRESH = "bff_rt"

app = FastAPI()

# -----------------------------------------------------------
# ✅ CORS FOR DEV
# -----------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------
# ✅ OIDC DISCOVERY (with retry)
# -----------------------------------------------------------

DISCOVERY = {}

async def ensure_discovery(retries=40, delay=2):
    global DISCOVERY

    if DISCOVERY:
        return DISCOVERY

    last_error = None

    async with httpx.AsyncClient() as client:
        for attempt in range(retries):
            for issuer in POSSIBLE_ISSUERS:
                url = f"{issuer}/.well-known/openid-configuration"
                try:
                    print(f"🔍 Attempt {attempt+1}: Trying {url}")
                    resp = await client.get(url, timeout=10)
                    resp.raise_for_status()

                    DISCOVERY = resp.json()
                    DISCOVERY["issuer"] = issuer  # save issuer used
                    print(f"✅ Discovery loaded from: {issuer}")
                    return DISCOVERY
                except Exception as e:
                    last_error = e

            await asyncio.sleep(delay)

    raise HTTPException(503, f"OIDC discovery unavailable: {last_error}")


@app.on_event("startup")
async def startup():
    asyncio.create_task(ensure_discovery())
    print("🚀 Backend started (lazy discovery enabled).")


# -----------------------------------------------------------
# ✅ TOKEN HANDLING
# -----------------------------------------------------------

async def exchange_code_for_tokens(code: str):
    disco = await ensure_discovery()
    token_url = disco["token_endpoint"]

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
    }

    if CLIENT_SECRET:
        data["client_secret"] = CLIENT_SECRET

    async with httpx.AsyncClient() as client:
        r = await client.post(token_url, data=data)
        r.raise_for_status()
        return r.json()


async def refresh_access_token(refresh_token: str):
    disco = await ensure_discovery()
    token_url = disco["token_endpoint"]

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
    }

    if CLIENT_SECRET:
        data["client_secret"] = CLIENT_SECRET

    async with httpx.AsyncClient() as client:
        r = await client.post(token_url, data=data)
        r.raise_for_status()
        return r.json()


# -----------------------------------------------------------
# ✅ AUTH ROUTES
# -----------------------------------------------------------

@app.get("/auth/login")
async def login():
    disco = await ensure_discovery()

    # Force browser URL to localhost:8080
    browser_authorize = disco["authorization_endpoint"]
    browser_authorize = browser_authorize.replace("http://keycloak:8080", "http://localhost:8080")
    browser_authorize = browser_authorize.replace("http://host.docker.internal:8080", "http://localhost:8080")

    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
    }

    url = f"{browser_authorize}?{urlencode(params)}"
    print("✅ Browser authorize URL:", url)

    return RedirectResponse(url)


@app.get("/auth/callback")
async def callback(request: Request):
    code = request.query_params.get("code")

    if not code:
        return JSONResponse({"error": "Missing authorization code"}, status_code=400)

    tokens = await exchange_code_for_tokens(code)

    resp = RedirectResponse("http://localhost:8081")  # front page after login
    resp.set_cookie(COOKIE_ACCESS, tokens["access_token"], httponly=True, samesite="strict")
    resp.set_cookie(COOKIE_REFRESH, tokens.get("refresh_token", ""), httponly=True, samesite="strict")

    return resp


# @app.get("/auth/logout")
# async def logout():
#     disco = await ensure_discovery()
#     end_session_endpoint = disco.get("end_session_endpoint")

#     redirect_after_logout = "http://localhost:8081"

#     # ✅ FULL LOGOUT: BFF + Keycloak SSO logout
#     url = (
#         f"{end_session_endpoint}"
#         f"?client_id={CLIENT_ID}"
#         f"&post_logout_redirect_uri={redirect_after_logout}"
#     )

#     resp = RedirectResponse(url)
#     resp.delete_cookie(COOKIE_ACCESS)
#     resp.delete_cookie(COOKIE_REFRESH)

#     return resp

@app.get("/auth/logout")
async def logout():
    disco = await ensure_discovery()
    end_session_endpoint = disco.get("end_session_endpoint")

    redirect_after_logout = "http://localhost:8081"

    # ✅ FIX: Ensure browser-facing URL
    browser_logout = end_session_endpoint
    browser_logout = browser_logout.replace("http://keycloak:8080", "http://localhost:8080")
    browser_logout = browser_logout.replace("http://host.docker.internal:8080", "http://localhost:8080")

    url = (
        f"{browser_logout}"
        f"?client_id={CLIENT_ID}"
        f"&post_logout_redirect_uri={redirect_after_logout}"
    )

    resp = RedirectResponse(url)
    resp.delete_cookie(COOKIE_ACCESS)
    resp.delete_cookie(COOKIE_REFRESH)

    return resp


# -----------------------------------------------------------
# ✅ AUTH DEPENDENCY
# -----------------------------------------------------------

async def require_auth(request: Request, response: Response):
    access = request.cookies.get(COOKIE_ACCESS)
    refresh = request.cookies.get(COOKIE_REFRESH)

    if not access:
        raise HTTPException(401, "Not authenticated")

    # Try decoding access token (ignore signature for BFF)
    try:
        jwt.decode(access, options={"verify_signature": False})
        return access
    except Exception:
        pass

    if not refresh:
        raise HTTPException(401, "Session expired")

    tokens = await refresh_access_token(refresh)

    response.set_cookie(COOKIE_ACCESS, tokens["access_token"], httponly=True, samesite="strict")

    if tokens.get("refresh_token"):
        response.set_cookie(COOKIE_REFRESH, tokens["refresh_token"], httponly=True, samesite="strict")

    return tokens["access_token"]


# -----------------------------------------------------------
# ✅ PROTECTED API
# -----------------------------------------------------------

# @app.get("/api/dashboard")
# async def dashboard(token=Depends(require_auth)):
#     claims = jwt.get_unverified_claims(token)
#     return {
#         "message": "Secure dashboard accessed!",
#         "user": claims.get("preferred_username"),
#         "time": time.time(),
#         "issuer_used": DISCOVERY.get("issuer"),
#     }

@app.get("/api/dashboard")
async def dashboard(token=Depends(require_auth)):
    claims = jwt.get_unverified_claims(token)

    roles = claims.get("realm_access", {}).get("roles", [])

    # ✅ Authorization check
    if "admin" not in roles:
        raise HTTPException(403, "You do not have permission to view dashboard")

    return {
        "message": "Secure dashboard accessed!",
        "user": claims.get("preferred_username"),
        "roles": roles,
        "time": time.time(),
        "issuer_used": DISCOVERY.get("issuer"),
    }

# -----------------------------------------------------------
# ✅ ROOT
# -----------------------------------------------------------

@app.get("/")
async def root():
    return {
        "status": "ok",
        "issuer_detected": DISCOVERY.get("issuer"),
        "possible_issuers": POSSIBLE_ISSUERS
    }

@app.get("/me")
async def me(token=Depends(require_auth)):
    claims = jwt.get_unverified_claims(token)
    return {
        "user": claims.get("preferred_username"),
        "roles": claims.get("realm_access", {}).get("roles", [])
    }

