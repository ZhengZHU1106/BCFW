import apiClient from './client'

export const systemAPI = {
  // 获取系统状态
  getStatus() {
    return apiClient.get('/v1/system/status')
  },

  // 模拟攻击
  simulateAttack() {
    return apiClient.post('/v1/attack/simulate')
  },

  // 获取提案列表
  getProposals() {
    return apiClient.get('/v1/proposals')
  },

  // 签署提案
  signProposal(proposalId, managerRole) {
    return apiClient.post(`/v1/proposals/${proposalId}/sign?manager_role=${managerRole}`)
  },

  // 手动创建提案
  createProposal(threatData) {
    return apiClient.post('/v1/proposals/create', threatData)
  },

  // 获取威胁检测日志
  getDetectionLogs() {
    return apiClient.get('/v1/logs/detections')
  },

  // 获取执行日志
  getExecutionLogs() {
    return apiClient.get('/v1/logs/executions')
  },

  // 向账户转账
  fundAccount(toAddress, amount = 1.0) {
    return apiClient.post('/v1/accounts/fund', {
      to_address: toAddress,
      amount: amount
    })
  },

  // 奖金池管理
  getRewardPoolInfo() {
    return apiClient.get('/v1/reward-pool/info')
  },

  getManagerContributions() {
    return apiClient.get('/v1/reward-pool/contributions')
  },

  depositToRewardPool(fromRole, amount) {
    return apiClient.post('/v1/reward-pool/deposit', {
      from_role: fromRole,
      amount_eth: amount
    })
  },

  // distributeContributionRewards API已移除 - 现在使用自动分配机制
}