<template>
  <div v-if="show" class="popup-overlay" @click.self="close">
    <div class="popup-card">
      <h3 class="popup-title">⚠ Permission Denied</h3>
      <p class="popup-message">{{ message }}</p>

      <button class="btn danger" @click="close">
        Close
      </button>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  show: Boolean,
  message: String
})

const emit = defineEmits(["close"])

const close = () => emit("close")
</script>

<style>
.popup-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  backdrop-filter: blur(6px);
  background: rgba(0,0,0,0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  animation: fadeIn 0.3s ease;
}

.popup-card {
  background: rgba(255, 255, 255, 0.12);
  padding: 2rem;
  width: 380px;
  border-radius: 16px;
  text-align: center;
  box-shadow: 0 8px 25px rgba(0,0,0,0.3);
  animation: slideUp 0.4s ease;
}

.popup-title {
  font-size: 1.5rem;
  margin-bottom: 1rem;
  background: linear-gradient(to right, #ff4444, #CC0000);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.popup-message {
  font-size: 1.1rem;
  color: #eee;
  margin-bottom: 1.5rem;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
</style>
