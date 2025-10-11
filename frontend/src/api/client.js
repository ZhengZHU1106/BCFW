import axios from 'axios'

// 创建axios实例
const apiClient = axios.create({
  baseURL: import.meta.env.PROD ? 'http://localhost:8000/api' : '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求去重：追踪pending请求
const pendingRequests = new Map()

// 生成请求key
const generateRequestKey = (config) => {
  const { method, url, params, data } = config
  return [method, url, JSON.stringify(params), JSON.stringify(data)].join('&')
}

// 请求拦截器
apiClient.interceptors.request.use(
  config => {
    const requestKey = generateRequestKey(config)

    // 检查是否有相同的pending请求
    if (pendingRequests.has(requestKey)) {
      console.log(`Request already pending: ${config.url}`)
      // 返回现有的pending promise
      return pendingRequests.get(requestKey)
    }

    // 创建cancel token
    const cancelToken = axios.CancelToken.source()
    config.cancelToken = cancelToken.token

    // 保存请求
    pendingRequests.set(requestKey, {
      cancel: cancelToken.cancel,
      timestamp: Date.now()
    })

    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  response => {
    // 移除已完成的请求
    const requestKey = generateRequestKey(response.config)
    pendingRequests.delete(requestKey)

    return response.data
  },
  error => {
    // 移除失败的请求
    if (error.config) {
      const requestKey = generateRequestKey(error.config)
      pendingRequests.delete(requestKey)
    }

    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// 定期清理超时的pending请求（防止内存泄漏）
setInterval(() => {
  const now = Date.now()
  const timeout = 60000 // 60秒
  for (const [key, value] of pendingRequests.entries()) {
    if (now - value.timestamp > timeout) {
      console.warn(`Cleaning up stale request: ${key}`)
      pendingRequests.delete(key)
    }
  }
}, 30000) // 每30秒清理一次

export default apiClient