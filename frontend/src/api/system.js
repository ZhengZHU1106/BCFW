import apiClient from './client'

export const systemAPI = {
  // 获取系统状态
  getStatus() {
    return apiClient.get('/system/status')
  },

  // 模拟攻击
  simulateAttack() {
    return apiClient.post('/attack/simulate')
  },

  // 获取提案列表
  getProposals() {
    return apiClient.get('/proposals')
  },

  // 签署提案
  signProposal(proposalId, managerIndex) {
    return apiClient.post(`/proposals/${proposalId}/sign`, {
      manager_index: managerIndex
    })
  },

  // 手动创建提案
  createProposal(threatData) {
    return apiClient.post('/proposals/create', threatData)
  },

  // 获取威胁检测日志
  getDetectionLogs() {
    return apiClient.get('/logs/detections')
  },

  // 获取执行日志
  getExecutionLogs() {
    return apiClient.get('/logs/executions')
  },

  // 向账户转账
  fundAccount(toAddress, amount = 1.0) {
    return apiClient.post('/accounts/fund', {
      to_address: toAddress,
      amount: amount
    })
  }
}