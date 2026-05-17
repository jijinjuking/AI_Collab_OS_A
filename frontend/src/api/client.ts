import axios from 'axios'
import { useAuthStore } from '@/store/auth'
import { toast } from '@/store/toast'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Global error handling
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err.response?.status
    const detail = err.response?.data?.detail

    if (status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
      return Promise.reject(err)
    }

    if (status === 403) {
      toast.error(detail || '无权执行此操作')
    } else if (status === 404) {
      toast.error(detail || '资源不存在')
    } else if (status === 409) {
      toast.warning(detail || '操作冲突，请刷新后重试')
    } else if (status === 422) {
      const errors = err.response?.data?.detail
      if (Array.isArray(errors)) {
        const msg = errors.map((e: any) => e.msg).join('; ')
        toast.error(`参数错误: ${msg}`)
      } else {
        toast.error(detail || '请求参数错误')
      }
    } else if (status && status >= 500) {
      toast.error('服务器错误，请稍后重试')
    } else if (err.code === 'ECONNABORTED') {
      toast.error('请求超时，请检查网络')
    } else if (!err.response) {
      toast.error('网络连接失败')
    }

    return Promise.reject(err)
  }
)

export default api
