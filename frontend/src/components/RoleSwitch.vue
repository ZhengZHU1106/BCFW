<template>
  <div class="role-switch">
    <label for="role-select">Role:</label>
    <select 
      id="role-select" 
      v-model="currentRole" 
      @change="handleRoleChange"
      class="role-select"
    >
      <option value="operator">Operator</option>
      <option value="manager">Manager</option>
    </select>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

// 当前角色状态（无状态，仅存储在localStorage）
const currentRole = ref('operator')

// 从localStorage读取角色
onMounted(() => {
  const savedRole = localStorage.getItem('userRole')
  if (savedRole && ['operator', 'manager'].includes(savedRole)) {
    currentRole.value = savedRole
  }
})

// 处理角色切换
const handleRoleChange = () => {
  localStorage.setItem('userRole', currentRole.value)
  // 触发自定义事件通知其他组件
  window.dispatchEvent(new CustomEvent('roleChanged', { 
    detail: { role: currentRole.value } 
  }))
}
</script>

<style scoped>
.role-switch {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.role-switch label {
  font-weight: 500;
  color: #ecf0f1;
}

.role-select {
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid #34495e;
  background-color: #34495e;
  color: white;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.role-select:hover {
  background-color: #2c3e50;
}

.role-select:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.5);
}
</style>