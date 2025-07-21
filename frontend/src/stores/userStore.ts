/**
 * 用户状态管理 Store
 * 管理当前用户角色、权限、偏好设置等
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type UserRole = 'operator_0' | 'operator_1' | 'operator_2' | 'operator_3' | 'operator_4' | 
                      'manager_0' | 'manager_1' | 'manager_2'

export interface UserProfile {
  role: UserRole
  displayName: string
  type: 'operator' | 'manager'
  permissions: string[]
  lastLoginAt?: string
  preferences: {
    theme: 'light' | 'dark'
    language: 'en' | 'zh'
    autoRefresh: boolean
    refreshInterval: number
  }
}

export const useUserStore = defineStore('user', () => {
  // State
  const currentRole = ref<UserRole>('operator_0')
  const profile = ref<UserProfile | null>(null)

  // Getters
  const userType = computed(() => {
    return currentRole.value.startsWith('manager') ? 'manager' : 'operator'
  })

  const displayName = computed(() => {
    const roleMap: Record<UserRole, string> = {
      'operator_0': 'Operator 0',
      'operator_1': 'Operator 1', 
      'operator_2': 'Operator 2',
      'operator_3': 'Operator 3',
      'operator_4': 'Operator 4',
      'manager_0': 'Manager 0',
      'manager_1': 'Manager 1',
      'manager_2': 'Manager 2'
    }
    return roleMap[currentRole.value] || currentRole.value
  })

  const permissions = computed(() => {
    const basePermissions = ['view_dashboard', 'view_threats', 'view_history']
    
    if (userType.value === 'operator') {
      return [
        ...basePermissions,
        'create_proposal',
        'simulate_attack',
        'view_detection_logs'
      ]
    } else {
      return [
        ...basePermissions,
        'sign_proposal', 
        'view_proposals',
        'manage_accounts',
        'access_reward_pool'
      ]
    }
  })

  const canCreateProposal = computed(() => {
    return permissions.value.includes('create_proposal')
  })

  const canSignProposal = computed(() => {
    return permissions.value.includes('sign_proposal')
  })

  const canManageAccounts = computed(() => {
    return permissions.value.includes('manage_accounts')
  })

  const canAccessRewardPool = computed(() => {
    return permissions.value.includes('access_reward_pool')
  })

  // Actions
  const switchRole = (newRole: UserRole) => {
    currentRole.value = newRole
    
    // 更新本地存储
    localStorage.setItem('userRole', newRole)
    
    // 更新用户配置
    updateProfile()
    
    // 触发角色变更事件
    window.dispatchEvent(new CustomEvent('roleChanged', { 
      detail: { role: newRole, type: userType.value } 
    }))
  }

  const updateProfile = () => {
    profile.value = {
      role: currentRole.value,
      displayName: displayName.value,
      type: userType.value,
      permissions: permissions.value,
      lastLoginAt: new Date().toISOString(),
      preferences: {
        theme: 'light',
        language: 'en',
        autoRefresh: true,
        refreshInterval: 5000
      }
    }
  }

  const initializeFromStorage = () => {
    // 从本地存储恢复角色
    const savedRole = localStorage.getItem('userRole') as UserRole
    if (savedRole && isValidRole(savedRole)) {
      currentRole.value = savedRole
    }
    
    updateProfile()
  }

  const isValidRole = (role: string): role is UserRole => {
    const validRoles: UserRole[] = [
      'operator_0', 'operator_1', 'operator_2', 'operator_3', 'operator_4',
      'manager_0', 'manager_1', 'manager_2'
    ]
    return validRoles.includes(role as UserRole)
  }

  const clearSession = () => {
    localStorage.removeItem('userRole')
    currentRole.value = 'operator_0'
    profile.value = null
  }

  const updatePreferences = (newPreferences: Partial<UserProfile['preferences']>) => {
    if (profile.value) {
      profile.value.preferences = {
        ...profile.value.preferences,
        ...newPreferences
      }
      
      // 保存到本地存储
      localStorage.setItem('userPreferences', JSON.stringify(profile.value.preferences))
    }
  }

  const loadPreferences = () => {
    try {
      const saved = localStorage.getItem('userPreferences')
      if (saved && profile.value) {
        const preferences = JSON.parse(saved)
        profile.value.preferences = {
          ...profile.value.preferences,
          ...preferences
        }
      }
    } catch (error) {
      console.error('Failed to load user preferences:', error)
    }
  }

  // 权限检查辅助方法
  const hasPermission = (permission: string): boolean => {
    return permissions.value.includes(permission)
  }

  const requirePermission = (permission: string): boolean => {
    if (!hasPermission(permission)) {
      throw new Error(`Permission denied: ${permission}`)
    }
    return true
  }

  return {
    // State
    currentRole,
    profile,
    
    // Getters
    userType,
    displayName,
    permissions,
    canCreateProposal,
    canSignProposal,
    canManageAccounts,
    canAccessRewardPool,
    
    // Actions
    switchRole,
    updateProfile,
    initializeFromStorage,
    clearSession,
    updatePreferences,
    loadPreferences,
    hasPermission,
    requirePermission
  }
})