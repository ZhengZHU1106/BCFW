/**
 * 威胁检测管理 Store
 * 管理威胁检测日志、威胁统计、攻击模拟等
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { systemAPI } from '@/api/system'

export interface ThreatDetection {
  id: string
  threat_type: string
  true_label: string
  confidence: number
  source_ip: string
  target_ip: string
  response_level: string
  action_taken: string
  status: 'detected' | 'pending' | 'executed'
  detected_at: string
  proposal_id?: string
  execution_log_id?: string
  detection_data?: any
  creating?: boolean
}

export interface ThreatStats {
  total: number
  high: number
  medium: number
  low: number
  blocked: number
  today: number
}

export interface ExecutionLog {
  id: string
  proposal_id?: string
  action_type: string
  target_ip: string
  success: boolean
  executed_at: string
  response_data?: any
}

export const useThreatStore = defineStore('threat', () => {
  // State
  const threats = ref<ThreatDetection[]>([])
  const executionLogs = ref<ExecutionLog[]>([])
  const latestThreat = ref<ThreatDetection | null>(null)
  const isLoading = ref(false)
  const isSimulating = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const threatStats = computed((): ThreatStats => {
    const stats = {
      total: threats.value.length,
      high: 0,
      medium: 0,
      low: 0,
      blocked: 0,
      today: 0
    }
    
    const today = new Date().toDateString()
    
    threats.value.forEach(threat => {
      // 按置信度分类
      if (threat.confidence > 0.8) {
        stats.high++
      } else if (threat.confidence > 0.5) {
        stats.medium++
      } else {
        stats.low++
      }
      
      // 已阻止的威胁
      if (threat.status === 'executed' || threat.action_taken === 'automatic_block') {
        stats.blocked++
      }
      
      // 今日检测
      if (new Date(threat.detected_at).toDateString() === today) {
        stats.today++
      }
    })
    
    return stats
  })

  const highRiskThreats = computed(() =>
    threats.value.filter(t => t.confidence > 0.8)
  )

  const recentThreats = computed(() =>
    threats.value
      .sort((a, b) => new Date(b.detected_at).getTime() - new Date(a.detected_at).getTime())
      .slice(0, 10)
  )

  const pendingThreats = computed(() =>
    threats.value.filter(t => t.status === 'pending' || t.status === 'detected')
  )

  // Actions
  const fetchDetectionLogs = async () => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await systemAPI.getDetectionLogs()
      
      if (response.success && response.data) {
        // 过滤掉 Benign 类型，因为这是威胁页面
        threats.value = response.data
          .filter((threat: ThreatDetection) => threat.threat_type !== 'Benign')
          .map((threat: ThreatDetection) => ({
            ...threat,
            creating: false
          }))
        
        // 更新最新威胁
        if (threats.value.length > 0) {
          latestThreat.value = threats.value[0]
        }
      } else {
        throw new Error(response.message || 'Failed to fetch detection logs')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch detection logs'
      console.error('Failed to fetch detection logs:', err)
    } finally {
      isLoading.value = false
    }
  }

  const fetchExecutionLogs = async () => {
    try {
      const response = await systemAPI.getExecutionLogs()
      
      if (response.success && response.data) {
        executionLogs.value = response.data
      }
    } catch (err) {
      console.error('Failed to fetch execution logs:', err)
    }
  }

  const simulateAttack = async () => {
    if (isSimulating.value) return
    
    isSimulating.value = true
    error.value = null
    
    try {
      const response = await systemAPI.simulateAttack()
      
      if (response.success && response.data) {
        const threatInfo = response.data.threat_info
        
        // 创建新的威胁记录
        const newThreat: ThreatDetection = {
          id: response.data.detection_id || Date.now().toString(),
          threat_type: threatInfo.true_label,
          true_label: threatInfo.true_label,
          confidence: threatInfo.confidence,
          source_ip: response.data.network_info?.source_ip || '192.168.1.100',
          target_ip: response.data.network_info?.target_ip || '192.168.1.1',
          response_level: threatInfo.response_level,
          action_taken: response.data.response_action?.action_taken || 'detected',
          status: response.data.response_action?.action_taken === 'automatic_block' ? 'executed' : 'detected',
          detected_at: response.data.timestamp || new Date().toISOString(),
          detection_data: response.data,
          creating: false
        }
        
        // 添加到威胁列表前端
        threats.value.unshift(newThreat)
        latestThreat.value = newThreat
        
        return response.data
      } else {
        throw new Error(response.message || 'Attack simulation failed')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Attack simulation failed'
      throw err
    } finally {
      isSimulating.value = false
    }
  }

  const createProposalForThreat = async (threat: ThreatDetection) => {
    if (threat.creating) return
    
    try {
      threat.creating = true
      
      const response = await systemAPI.createProposal({
        detection_id: threat.id,
        action: 'block',
        operator_role: 'operator_0' // 可以从用户store获取
      })
      
      if (response.success) {
        // 更新威胁状态
        threat.status = 'pending'
        threat.proposal_id = response.data.id
        
        return response.data
      } else {
        throw new Error(response.message || 'Failed to create proposal')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to create proposal'
      throw err
    } finally {
      threat.creating = false
    }
  }

  const getThreat = (threatId: string): ThreatDetection | undefined => {
    return threats.value.find(t => t.id === threatId)
  }

  const canCreateProposal = (threat: ThreatDetection): boolean => {
    return threat.status === 'detected' && 
           threat.confidence >= 0.7 && 
           threat.confidence < 0.8 &&
           !threat.proposal_id
  }

  const clearError = () => {
    error.value = null
  }

  // 自动刷新机制
  let refreshInterval: number | null = null

  const startAutoRefresh = (intervalMs: number = 10000) => {
    if (refreshInterval) {
      clearInterval(refreshInterval)
    }
    
    refreshInterval = setInterval(() => {
      fetchDetectionLogs()
    }, intervalMs)
  }

  const stopAutoRefresh = () => {
    if (refreshInterval) {
      clearInterval(refreshInterval)
      refreshInterval = null
    }
  }

  return {
    // State
    threats,
    executionLogs,
    latestThreat,
    isLoading,
    isSimulating,
    error,
    
    // Getters
    threatStats,
    highRiskThreats,
    recentThreats,
    pendingThreats,
    
    // Actions
    fetchDetectionLogs,
    fetchExecutionLogs,
    simulateAttack,
    createProposalForThreat,
    getThreat,
    canCreateProposal,
    clearError,
    startAutoRefresh,
    stopAutoRefresh
  }
})