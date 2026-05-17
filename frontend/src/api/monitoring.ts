import axios from 'axios'

// Monitoring endpoints have no /api/v1 prefix and no auth
const monitorApi = axios.create({
  baseURL: '',
  timeout: 10000,
})

export interface HealthResponse {
  status: string
  app: string
  env: string
  version: string
}

export interface DetailedHealthResponse extends HealthResponse {
  uptime: string
  uptime_seconds: number
  timestamp: string
  checks: {
    database: { status: string; error?: string }
    redis: { status: string; error?: string }
  }
}

export interface MetricsResponse {
  database_pool: {
    pool_size: number
    checked_in: number
    checked_out: number
    overflow: number
  }
  websocket: {
    active_rooms: number
    total_connections: number
    rooms: Record<string, number>
  }
  redis_connected: boolean
}

export const monitoringApi = {
  health: () => monitorApi.get<HealthResponse>('/health'),

  detailedHealth: () =>
    monitorApi.get<DetailedHealthResponse>('/health/detailed'),

  metrics: () => monitorApi.get<MetricsResponse>('/metrics'),
}
