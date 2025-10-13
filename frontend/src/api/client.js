import axios from 'axios'

// 创建axios实例
const apiClient = axios.create({
  baseURL: import.meta.env.PROD ? 'http://localhost:8000/api' : '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求去重：追踪pending请求的Promise
const pendingRequests = new Map()

// 生成请求key
const generateRequestKey = (config) => {
  const { method, url, params, data } = config
  return [method, url, JSON.stringify(params), JSON.stringify(data)].join('&')
}

// 包装axios请求以支持去重
const originalRequest = apiClient.request.bind(apiClient)
apiClient.request = function(config) {
  const requestKey = generateRequestKey(config)

  // 如果有相同的pending请求，返回现有Promise
  if (pendingRequests.has(requestKey)) {
    console.log(`Request already pending: ${config.url}, reusing existing request`)
    return pendingRequests.get(requestKey)
  }

  // 创建新的请求Promise
  const requestPromise = originalRequest(config)
    .then(response => {
      // 请求成功，清理pending记录
      pendingRequests.delete(requestKey)
      return response
    })
    .catch(error => {
      // 请求失败，清理pending记录
      pendingRequests.delete(requestKey)
      throw error
    })

  // 保存Promise供后续重复请求使用
  pendingRequests.set(requestKey, requestPromise)

  return requestPromise
}

// 响应拦截器 - 只负责数据转换
apiClient.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// 定期清理超时的pending请求（防止内存泄漏）
setInterval(() => {
  const now = Date.now()
  const timeout = 60000 // 60秒
  // 清理所有pending请求（因为我们现在存储的是Promise，无法判断时间戳）
  // 正常情况下请求会在完成后自动清理，这只是兜底机制
  if (pendingRequests.size > 100) {
    console.warn(`Clearing ${pendingRequests.size} pending requests to prevent memory leak`)
    pendingRequests.clear()
  }
}, 30000) // 每30秒检查一次

export default apiClient