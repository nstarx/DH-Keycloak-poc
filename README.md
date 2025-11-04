# 🔐 Keycloak + FastAPI + Vue 3 POC (Production-Ready)

## 🧠 Overview

This repository demonstrates a **complete authentication and authorization workflow** using:

- **Keycloak** → Identity and Access Management (IAM)
- **FastAPI** → Backend service with protected routes
- **Vue 3 (Vite)** → Frontend application integrated with Keycloak JS adapter
- **Docker Compose** → To run all services in isolated containers

The project showcases **OAuth2.0 + OpenID Connect (OIDC)** login flow, **role-based access control (RBAC)**, and **secure API calls** from frontend to backend.

---

## ⚙️ Architecture Overview

```
                ┌─────────────────────┐
                │      Keycloak       │
                │ (Auth Server)       │
                │ http://localhost:8080│
                └──────────┬──────────┘
                           │
         Token (JWT)       │
                           ▼
┌───────────────────────────────┐       Protected API call
│           FastAPI             │◄────────────────────────┐
│  Backend (http://localhost:8000)                        │
│  Validates JWT using Keycloak public keys               │
│  and role-based access control                          │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
      ┌─────────────────────┐
      │      Vue 3 App      │
      │  (http://localhost:5173) │
      │  Uses keycloak-js for login/logout   │
      └─────────────────────┘
```

---

## 🐳 Services Overview

| Service   | Description | Port | URL |
|------------|--------------|------|-----|
| **keycloak** | Auth server for user and role management | 8080 | [http://localhost:8080](http://localhost:8080) |
| **backend** | FastAPI backend that validates JWT tokens | 8000 | [http://localhost:8000/docs](http://localhost:8000/docs) |
| **frontend** | Vue 3 (Vite) frontend integrated with Keycloak | 5173 | [http://localhost:5173](http://localhost:5173) |

---

## 🧰 Prerequisites

Before starting, ensure you have:

- [Docker](https://www.docker.com/) & Docker Compose
- Node.js ≥ 18
- Python ≥ 3.10

---

## 🚀 Getting Started

### 1️⃣ Clone the repo

```bash
git clone https://github.com/your-username/keycloak-fastapi-vue-poc.git
cd keycloak-fastapi-vue-poc
```

---

### 2️⃣ Setup Keycloak

1. Start Keycloak container:

   ```bash
   docker-compose up -d keycloak
   ```

2. Visit [http://localhost:8080](http://localhost:8080)

3. Login to the admin console:  
   - **Username:** `admin`  
   - **Password:** `admin`

4. Create a new **Realm** named:  
   `demo-realm`

5. Inside `demo-realm`, create a **Client**:
   - **Client ID:** `vue-client`
   - **Access Type:** `public`
   - **Valid Redirect URIs:** `http://localhost:5173/*`
   - **Web Origins:** `*`
   - **Root URL:** `http://localhost:5173`

6. Create a **Role**:
   - Name: `dashboard`
   - Save it.

7. Create a **User**:
   - Username: `demo`
   - Set a password (`demo`)
   - Assign the role `dashboard`.

---

### 3️⃣ Backend Setup (FastAPI)

**Directory:** `/backend`

#### a. Install dependencies

```bash
pip install -r requirements.txt
```

#### b. Run standalone (optional)

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### c. Key Points

- Uses `python-jose` to decode and verify JWT.
- Token issuer and audience are verified against Keycloak’s `/.well-known/openid-configuration`.
- Protected route `/dashboard` checks for role `"user"`.

#### Example Protected Endpoint
```python
@app.get("/dashboard")
async def read_dashboard(user: dict = Depends(get_current_user)):
    if "user" not in user["roles"]:
        raise HTTPException(status_code=403, detail="Insufficient role")
    return {"message": f"Welcome {user['preferred_username']}!"}
```

---

### 4️⃣ Frontend Setup (Vue 3 + Vite)

**Directory:** `/frontend`

#### a. Install dependencies

```bash
npm install
```

#### b. Keycloak Integration

- Located in `/frontend/src/keycloak.js`:

```js
import Keycloak from "keycloak-js";

const keycloak = new Keycloak({
  url: "http://localhost:8080",
  realm: "demo-realm",
  clientId: "vue-client",
});

export default keycloak;
```

#### c. Start frontend

```bash
npm run dev
```

#### d. Pages

- `Home.vue` → Public, shows login/logout and username.
- `Dashboard.vue` → Protected route; requires valid role to access.

---

### 5️⃣ Run Everything in Docker

#### Build and run all containers:

```bash
docker-compose up --build
```

It starts:
- Keycloak on port **8080**
- FastAPI backend on **8000**
- Vue frontend on **5173**

#### Stop containers:

```bash
docker-compose down
```

---

## 🧩 Login Flow Summary

1. User visits `http://localhost:5173`
2. Clicks **Login** → redirected to Keycloak login.
3. Upon successful login:
   - Keycloak returns a **JWT access token**
   - Vue stores the token in memory.
4. Clicking “Dashboard” calls FastAPI’s `/dashboard` endpoint with:
   ```http
   Authorization: Bearer <access_token>
   ```
5. FastAPI verifies:
   - Signature (via Keycloak’s public key)
   - Issuer & audience
   - Roles
6. If valid → returns `200 OK` with a welcome message.

---

## 🔍 Common Issues & Fixes

| Problem | Reason | Fix |
|----------|---------|-----|
| `401 Unauthorized` | Token issuer mismatch | Ensure backend uses same issuer as Keycloak (e.g., `http://localhost:8080/realms/demo-realm`) |
| `Insufficient role` | User lacks required role | In Keycloak Admin Console → Add role “user” under the user’s Role Mappings |
| Keycloak not accessible in Docker | Wrong hostname | If backend and keycloak run in different containers, set `KEYCLOAK_URL=http://keycloak:8080` inside backend container |
| Frontend not showing username after navigation | Session not checked | Use `onLoad: 'check-sso'` in Keycloak init to persist login session |
| CORS errors | Backend missing headers | Add `CORSMiddleware` in FastAPI |

---

## ⚡ Example Environment Variables

`.env` for backend:

```bash
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=demo-realm
KEYCLOAK_CLIENT_ID=vue-client
KEYCLOAK_AUDIENCE=account
```

---

## 🔐 Role-Based Access Example

| User | Roles | Can Access `/dashboard`? |
|------|--------|--------------------------|
| demo | user | ✅ Yes |
| admin | admin | ❌ No (unless “user” also added) |

---

## 🧭 Project Structure

```
.
├── backend
│   ├── main.py
│   ├── auth.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend
│   ├── src/
│   │   ├── views/
│   │   │   ├── Home.vue
│   │   │   └── Dashboard.vue
│   │   └── keycloak.js
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml
└── README.md
```

---

## 🧪 Testing the Setup

1. Go to [http://localhost:5173](http://localhost:5173)
2. Click **Login**
3. Login with:
   ```
   username: demo
   password: demo
   ```
4. You should see:
   ```
   Welcome demo 👋
   ```
5. Click **Go to Dashboard**
6. Backend should log:
   ```
   ✅ Token verified for user demo
   ```
   and return a 200 OK.

---

## 🔐 Security Notes

- Do **not** store access tokens in localStorage — only keep them in memory.
- Use HTTPS in production.
- Use **PKCE (Proof Key for Code Exchange)** for better security (`pkceMethod: 'S256'`).

---

## 🧰 Useful Commands

| Command | Description |
|----------|-------------|
| `docker-compose up --build` | Build and start all containers |
| `docker-compose logs -f backend` | View backend logs |
| `docker-compose down` | Stop containers |
| `npm run dev` | Run frontend locally |
| `uvicorn main:app --reload` | Run backend locally |

---

## 🏁 Conclusion

This POC demonstrates how to integrate **Keycloak**, **FastAPI**, and **Vue 3** with:
- OAuth2/OIDC login
- Role-based access control
- Secure backend API validation
- Docker-based local deployment

Once validated, this architecture can be easily extended to **microservices**, **multi-role dashboards**, or **enterprise SSO integrations**.

---
