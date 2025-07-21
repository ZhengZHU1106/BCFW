/**
 * 提案管理 Store
 * 管理多重签名提案的创建、签名、执行等状态
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { systemAPI } from '@/api/system'

export interface Proposal {
  id: string
  threat_type: string
  confidence: number
  true_label: string
  proposal_type: string
  target_ip: string
  action_type: string
  status: 'pending' | 'approved' | 'rejected' | 'executed'
  signatures_count: number
  signatures_required: number
  signed_by: string[]
  final_signer?: string
  created_at: string
  approved_at?: string
  contract_proposal_id?: number
  contract_address?: string
  detection_data?: any
}

export interface ProposalStats {
  total: number
  pending: number
  approved: number
  rejected: number
  executed: number
}

export const useProposalStore = defineStore('proposal', () => {
  // State
  const proposals = ref<Proposal[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const currentFilter = ref<'all' | 'pending' | 'approved' | 'rejected' | 'executed'>('all')

  // Getters
  const filteredProposals = computed(() => {
    if (currentFilter.value === 'all') {
      return proposals.value
    }
    return proposals.value.filter(p => p.status === currentFilter.value)
  })

  const proposalStats = computed((): ProposalStats => {
    const stats = {
      total: proposals.value.length,
      pending: 0,
      approved: 0,
      rejected: 0,
      executed: 0
    }
    
    proposals.value.forEach(proposal => {
      switch (proposal.status) {
        case 'pending':
          stats.pending++
          break
        case 'approved':
          stats.approved++
          break
        case 'rejected':
          stats.rejected++
          break
        case 'executed':
          stats.executed++
          break
      }
    })
    
    return stats
  })

  const pendingProposals = computed(() => 
    proposals.value.filter(p => p.status === 'pending')
  )

  const recentProposals = computed(() => 
    proposals.value
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 5)
  )

  // Actions
  const fetchProposals = async () => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await systemAPI.getProposals()
      
      if (response.success && response.data) {
        // API返回的是分类的提案对象，需要合并为数组
        proposals.value = [
          ...(response.data.pending || []),
          ...(response.data.approved || []),
          ...(response.data.rejected || [])
        ]
      } else {
        throw new Error(response.message || 'Failed to fetch proposals')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch proposals'
      console.error('Failed to fetch proposals:', err)
    } finally {
      isLoading.value = false
    }
  }

  const createProposal = async (threatData: any) => {
    try {
      const response = await systemAPI.createProposal(threatData)
      
      if (response.success && response.data) {
        // 添加新提案到列表
        proposals.value.unshift(response.data)
        return response.data
      } else {
        throw new Error(response.message || 'Failed to create proposal')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to create proposal'
      throw err
    }
  }

  const signProposal = async (proposalId: string, managerId: string) => {
    try {
      const response = await systemAPI.signProposal(proposalId, managerId)
      
      if (response.success) {
        // 刷新提案列表以获取最新状态
        await fetchProposals()
        return response
      } else {
        throw new Error(response.message || 'Failed to sign proposal')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to sign proposal'
      throw err
    }
  }

  const getProposal = (proposalId: string): Proposal | undefined => {
    return proposals.value.find(p => p.id === proposalId)
  }

  const canUserSignProposal = (proposal: Proposal, userRole: string): boolean => {
    // 检查用户是否可以签名此提案
    if (proposal.status !== 'pending') return false
    if (!userRole.startsWith('manager')) return false
    
    return !proposal.signed_by.includes(userRole)
  }

  const setFilter = (filter: typeof currentFilter.value) => {
    currentFilter.value = filter
  }

  const clearError = () => {
    error.value = null
  }

  // 自动刷新机制
  let refreshInterval: number | null = null

  const startAutoRefresh = (intervalMs: number = 5000) => {
    if (refreshInterval) {
      clearInterval(refreshInterval)
    }
    
    refreshInterval = setInterval(() => {
      fetchProposals()
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
    proposals,
    isLoading,
    error,
    currentFilter,
    
    // Getters
    filteredProposals,
    proposalStats,
    pendingProposals,
    recentProposals,
    
    // Actions
    fetchProposals,
    createProposal,
    signProposal,
    getProposal,
    canUserSignProposal,
    setFilter,
    clearError,
    startAutoRefresh,
    stopAutoRefresh
  }
})