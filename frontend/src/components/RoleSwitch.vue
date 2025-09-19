<template>
  <div class="role-switch">
    <label for="role-select">Role:</label>
    <select 
      id="role-select" 
      v-model="currentRole" 
      @change="handleRoleChange"
      class="role-select"
    >
      <optgroup label="Operators">
        <option value="operator_0">Operator 0</option>
        <option value="operator_1">Operator 1</option>
        <option value="operator_2">Operator 2</option>
        <option value="operator_3">Operator 3</option>
        <option value="operator_4">Operator 4</option>
      </optgroup>
      <optgroup label="Managers">
        <option value="manager_0">Manager 0</option>
        <option value="manager_1">Manager 1</option>
        <option value="manager_2">Manager 2</option>
      </optgroup>
    </select>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

// 防抖函数实现
function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

// 当前角色状态（无状态，仅存储在localStorage）
const currentRole = ref('operator_0')

// 有效角色列表
const validRoles = [
  'operator_0', 'operator_1', 'operator_2', 'operator_3', 'operator_4',
  'manager_0', 'manager_1', 'manager_2'
]

// 从localStorage读取角色
onMounted(() => {
  const savedRole = localStorage.getItem('userRole')
  if (savedRole && validRoles.includes(savedRole)) {
    currentRole.value = savedRole
  }
})

// 处理角色切换的核心逻辑
const doRoleChange = () => {
  localStorage.setItem('userRole', currentRole.value)
  // 触发自定义事件通知其他组件
  window.dispatchEvent(new CustomEvent('roleChanged', {
    detail: { role: currentRole.value }
  }))
}

// 防抖的角色切换处理器 (300ms 防抖，避免快速切换导致的频繁事件)
const handleRoleChange = debounce(doRoleChange, 300)
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