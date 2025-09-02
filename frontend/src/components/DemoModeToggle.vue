<template>
  <div class="demo-mode-toggle">
    <label class="toggle-switch">
      <input 
        type="checkbox" 
        v-model="isDemoMode" 
        @change="handleModeChange"
      />
      <span class="slider"></span>
    </label>
    <span class="toggle-label">
      {{ isDemoMode ? 'Demo Mode' : 'Role Mode' }}
    </span>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

// Demo mode state
const isDemoMode = ref(false)

// Load demo mode state from localStorage
onMounted(() => {
  const savedMode = localStorage.getItem('demoMode')
  if (savedMode === 'true') {
    isDemoMode.value = true
  }
})

// Handle mode change
const handleModeChange = () => {
  localStorage.setItem('demoMode', isDemoMode.value.toString())
  
  // Dispatch custom event to notify other components
  window.dispatchEvent(new CustomEvent('demoModeChanged', { 
    detail: { isDemoMode: isDemoMode.value } 
  }))
}
</script>

<style scoped>
.demo-mode-toggle {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-left: 1rem;
}

.toggle-label {
  font-weight: 500;
  color: #ecf0f1;
  font-size: 0.9rem;
  min-width: 80px;
}

/* Toggle Switch Styles */
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 24px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #34495e;
  transition: all 0.3s;
  border-radius: 24px;
  border: 2px solid #2c3e50;
}

.slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 2px;
  bottom: 2px;
  background-color: #ecf0f1;
  transition: all 0.3s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #3498db;
  border-color: #2980b9;
}

input:focus + .slider {
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.3);
}

input:checked + .slider:before {
  transform: translateX(24px);
}

.slider:hover {
  background-color: #2c3e50;
}

input:checked + .slider:hover {
  background-color: #2980b9;
}
</style>