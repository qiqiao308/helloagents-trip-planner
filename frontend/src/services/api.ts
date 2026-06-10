import axios from 'axios'
import type { TripPlanRequest, TripPlan } from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 180000, // 3 分钟（LLM 调用可能较慢）
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('📤 发送请求:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => Promise.reject(error),
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log('📥 收到响应:', response.status)
    return response
  },
  (error) => {
    const msg = error.response?.data?.detail || error.message || '请求失败'
    console.error('❌ 请求失败:', msg)
    return Promise.reject(new Error(msg))
  },
)

/** 生成旅行计划 */
export const generateTripPlan = async (request: TripPlanRequest): Promise<TripPlan> => {
  const response = await api.post<TripPlan>('/trip/plan', request)
  return response.data
}
