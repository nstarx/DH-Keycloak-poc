<template>
  <div class="home-container">
    <div class="card">
      <h1 class="title">🔐 Keycloak Vue POC</h1>

      <div v-if="!authenticated" class="auth-section">
        <p class="status">You are not logged in.</p>
        <button class="btn primary" @click="login">Login with Keycloak</button>
      </div>

      <div v-else class="auth-section">
        <p class="status">Welcome, <strong>{{ profile?.preferred_username }}</strong> 👋</p>
        <div class="btn-group">
          <button class="btn success" @click="goDashboard">Go to Dashboard</button>
          <button class="btn danger" @click="logout">Logout</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import keycloak from '../keycloak'
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

export default {
  setup() {
    const router = useRouter()
    const authenticated = ref(false)
    const profile = ref(null)

    onMounted(async () => {
      try {
        await keycloak.init({ onLoad: 'check-sso', pkceMethod: 'S256' })
        authenticated.value = keycloak.authenticated
        if (authenticated.value) {
          profile.value = keycloak.tokenParsed
        }
        console.log('KC initialized, authenticated=', profile)
      } catch (err) {
        console.error('KC init error', err)
      }
    })

    const login = () => keycloak.login()
    const logout = () => keycloak.logout({ redirectUri: window.location.origin })
    const goDashboard = async () => {
      try {
        const token = keycloak.token
        await axios.get('http://localhost:8000/dashboard', {
          headers: { Authorization: `Bearer ${token}` }
        })
        router.push({ name: 'Dashboard' })
      } catch (e) {
        alert('Backend denied access: ' + (e?.response?.data?.detail || e.message))
      }
    }

    return { authenticated, profile, login, logout, goDashboard }
  }
}
</script>

<style scoped>
/* Background */
.home-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #1A3636, #0F2027);
  color: #fff;
  font-family: 'Poppins', sans-serif;
}

/* Card box */
.card {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 3rem;
  text-align: center;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
  transition: transform 0.4s ease, box-shadow 0.4s ease;
  width: 400px;
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
}

/* Title */
.title {
  font-size: 2rem;
  margin-bottom: 1.5rem;
  background: linear-gradient(to right, #FFD700, #FFAE00);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* Text */
.status {
  font-size: 1.1rem;
  margin-bottom: 2rem;
  color: #ddd;
}

/* Button group */
.btn-group {
  display: flex;
  justify-content: center;
  gap: 1rem;
}

/* Buttons */
.btn {
  padding: 0.8rem 1.5rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  transition: all 0.3s ease;
  color: #fff;
  box-shadow: 0 3px 10px rgba(0,0,0,0.2);
}

.btn.primary {
  background: linear-gradient(90deg, #FFAE00, #FFD700);
  color: #222;
}

.btn.primary:hover {
  transform: scale(1.05);
  box-shadow: 0 0 15px #FFD700;
}

.btn.success {
  background: linear-gradient(90deg, #00C851, #007E33);
}

.btn.success:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 15px #00C851;
}

.btn.danger {
  background: linear-gradient(90deg, #ff4444, #CC0000);
}

.btn.danger:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 15px #ff4444;
}

/* Smooth fade-in animation */
.card {
  animation: fadeIn 0.8s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
