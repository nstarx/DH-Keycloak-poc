<template>
  <div class="dashboard-container">
    <div class="card">
      <div class="header">
        <h2 class="title">📊 Dashboard</h2>
        <div class="header-buttons">
          <button class="btn secondary" @click="goBack">⬅ Back</button>
          <button class="btn danger" @click="logout">Logout</button>
        </div>
      </div>

      <div class="content">
        <pre v-if="meta" class="data-box">{{ JSON.stringify(meta, null, 2) }}</pre>
        <p v-else class="loading">Loading...</p>
      </div>

      <div class="actions">
        <button class="btn primary" @click="refresh">🔄 Refresh</button>
      </div>
    </div>
  </div>
</template>

<script>
import keycloak from '../keycloak'
import axios from 'axios'
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

export default {
  setup() {
    const meta = ref(null)
    const router = useRouter()

    const fetchMeta = async () => {
      const token = keycloak.token
      try {
        const resp = await axios.get('http://localhost:8000/dashboard', {
          headers: { Authorization: `Bearer ${token}` }
        })
        meta.value = resp.data
      } catch (e) {
        meta.value = { error: e?.response?.data?.detail || e.message }
      }
    }

    const logout = () => {
      keycloak.logout({ redirectUri: window.location.origin })
      router.push('/')
    }

    // 🟨 New Back button handler
    const goBack = () => {
      if (window.history.length > 1) {
        router.back()
      } else {
        router.push('/') // fallback if no history
      }
    }

    onMounted(fetchMeta)
    return { meta, refresh: fetchMeta, logout, goBack }
  }
}
</script>

<style scoped>
.dashboard-container {
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
  text-align: left;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
  transition: transform 0.4s ease, box-shadow 0.4s ease;
  width: 600px;
  animation: fadeIn 0.8s ease-in-out;
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* Align Logout & Back together */
.header-buttons {
  display: flex;
  gap: 10px;
}

/* Title */
.title {
  font-size: 1.8rem;
  background: linear-gradient(to right, #FFD700, #FFAE00);
  -webkit-background-clip: text;
  color: #FFD700;
}

.data-box {
  background-color: rgba(255, 255, 255, 0.07);
  padding: 1rem;
  border-radius: 8px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 300px;
  margin-top: 1.5rem;
  color: #f2f2f2;
  font-size: 0.95rem;
}

.loading {
  margin-top: 2rem;
  font-size: 1.1rem;
  color: #ccc;
  text-align: center;
}

/* Buttons */
.btn {
  padding: 0.7rem 1.5rem;
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

.btn.danger {
  background: linear-gradient(90deg, #ff4444, #CC0000);
}

.btn.danger:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 15px #ff4444;
}

/* Back Button (Secondary) */
.btn.secondary {
  background: linear-gradient(90deg, #1E90FF, #00BFFF);
}

.btn.secondary:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 15px #00BFFF;
}

.actions {
  display: flex;
  justify-content: center;
  margin-top: 1.5rem;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
