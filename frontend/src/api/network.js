import apiClient from './client'

export const networkAPI = {
  // 获取网络拓扑
  getTopology: () => {
    return apiClient.get('/v1/network/topology')
  },

  // 获取节点详细信息
  getNodeDetails: (nodeId) => {
    return apiClient.get(`/v1/network/nodes/${nodeId}/details`)
  },

  // 模拟攻击流程
  simulateAttackFlow: (params) => {
    return apiClient.post('/v1/network/simulate-attack-flow', params)
  },

  // 获取可用节点索引
  getAvailableIndices: () => {
    return apiClient.get('/v1/network/nodes/available-indices')
  },

  // 创建新节点
  createNode: (params) => {
    return apiClient.post('/v1/network/nodes/create', params)
  },

  // 删除节点
  removeNode: (nodeId) => {
    return apiClient.delete(`/v1/network/nodes/${nodeId}/remove`)
  }
}