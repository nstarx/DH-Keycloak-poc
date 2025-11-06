<script setup>
import axios from "axios"
import { ref } from "vue"
import { useRouter } from "vue-router"

const router = useRouter()

// ✅ Track login state & username
const isLoggedIn = ref(false)
const username = ref(null)

// ✅ Detect login on page load
const checkLogin = async () => {
  try {
    const res = await axios.get("http://localhost:8000/me", {
      withCredentials: true,
    })
    isLoggedIn.value = true
    username.value = res.data.user
  } catch {
    isLoggedIn.value = false
    username.value = null
  }
}

checkLogin()

const login = () => {
  window.location.href = "http://localhost:8000/auth/login"
}

const logout = () => {
  isLoggedIn.value = false
  username.value = null
  window.location.href = "http://localhost:8000/auth/logout"
}

const goDashboard = async () => {
  try {
    const res = await axios.get("http://localhost:8000/api/dashboard", {
      withCredentials: true,
    })

    const roles = res.data.roles || []

    if (!roles.includes("admin")) {
      alert("❌ You do not have permission to view the dashboard.")
      return
    }

    router.push("/dashboard")

  } catch {
    alert("❌ You do not have permission to view the dashboard.")
  }
}
</script>


<template>
  <div class="home-container">
    <div class="card">

      <h2 class="title">Vue + FastAPI BFF Auth</h2>

      <p class="status">
        <span v-if="isLoggedIn">✅ Welcome, {{ username || "User" }}!</span>
        <span v-else>❌ Please log in</span>
      </p>

      <div class="btn-group">
        <!-- ✅ Show Login when logged out -->
        <button v-if="!isLoggedIn" class="btn primary" @click="login">
          Login
        </button>

        <!-- ✅ Show Logout when logged in -->
        <button v-if="isLoggedIn" class="btn danger" @click="logout">
          Logout
        </button>

        <!-- ✅ Dashboard always visible -->
        <button class="btn success" @click="goDashboard">
          Go to Dashboard
        </button>
      </div>
    </div>
  </div>
</template>

<style>
/* ✅ Your complete CSS — unchanged */
.home-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #1A3636, #0F2027);
  color: #fff;
  font-family: 'Poppins', sans-serif;
}

.card {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 3rem;
  text-align: center;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
  transition: transform 0.4s ease, box-shadow 0.4s ease;
  width: 400px;
  animation: fadeIn 0.8s ease-in-out;
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
}

.title {
  font-size: 2rem;
  margin-bottom: 1.5rem;
  background: linear-gradient(to right, #FFD700, #FFAE00);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.status {
  font-size: 1.1rem;
  margin-bottom: 2rem;
  color: #ddd;
}

.btn-group {
  display: flex;
  justify-content: center;
  gap: 1rem;
}

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

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
