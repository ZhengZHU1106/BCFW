import apiClient from './client'

export const networkAPI = {
  // 获取网络拓扑
  getTopology: () => {
    return apiClient.get('/network/topology')
  },

  // 获取节点详细信息
  getNodeDetails: (nodeId) => {
    return apiClient.get(`/network/nodes/${nodeId}/details`)
  },

  // 模拟攻击流程
  simulateAttackFlow: (params) => {
    return apiClient.post('/network/simulate-attack-flow', params)
  },

  // 获取可用节点索引 (Deprecated - 仅用于向后兼容)
  getAvailableIndices: () => {
    return apiClient.get('/network/nodes/available-indices')
  },

  // 获取可显示的隐藏节点列表 (New)
  getAvailableNodes: () => {
    return apiClient.get('/network/nodes/available')
  },

  // 显示隐藏的节点 (New)
  showNode: (nodeId) => {
    return apiClient.post('/network/nodes/show', { node_id: nodeId })
  },

  // 隐藏节点 (New)
  hideNode: (nodeId) => {
    return apiClient.post('/network/nodes/hide', { node_id: nodeId })
  },

  // 创建新节点 (Deprecated - DevLeChain不支持动态创建)
  createNode: (params) => {
    return apiClient.post('/network/nodes/create', params)
  },

  // 删除节点 (Deprecated - 保留用于向后兼容)
  removeNode: (nodeId) => {
    return apiClient.delete(`/network/nodes/${nodeId}/remove`)
  },

  // 注册账户为网络节点
  registerAccountAsNode: (params) => {
    return apiClient.post('/network/nodes/register', params)
  }
}