import { useEffect, useState } from 'react'
import { monitoringApi, DetailedHealthResponse, MetricsResponse } from '@/api/monitoring'
import '@/styles/dashboard.css'

export default function DashboardPage() {
  const [health, setHealth] = useState<DetailedHealthResponse | null>(null)
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)

  const fetchData = async () => {
    try {
      const [healthRes, metricsRes] = await Promise.all([
        monitoringApi.detailedHealth(),
        monitoringApi.metrics(),
      ])
      setHealth(healthRes.data)
      setMetrics(metricsRes.data)
      setError(null)
    } catch (e: any) {
      setError(e.message || '无法连接到服务器')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  useEffect(() => {
    if (!autoRefresh) return
    const timer = setInterval(fetchData, 5000)
    return () => clearInterval(timer)
  }, [autoRefresh])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'status-healthy'
      case 'ok': return 'status-healthy'
      case 'degraded': return 'status-degraded'
      default: return 'status-unhealthy'
    }
  }

  if (loading) {
    return <div className="dashboard-page"><div className="loading">加载监控数据...</div></div>
  }

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1>系统监控</h1>
        <div className="header-actions">
          <label className="auto-refresh-toggle">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            自动刷新 (5s)
          </label>
          <button className="btn-secondary" onClick={fetchData}>
            刷新
          </button>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <span>⚠️ {error}</span>
        </div>
      )}

      {/* Overall Status */}
      {health && (
        <section className="status-overview">
          <div className={`overall-status ${getStatusColor(health.status)}`}>
            <div className="status-indicator" />
            <div className="status-info">
              <h2>{health.app}</h2>
              <p>
                状态: <strong>{health.status === 'healthy' ? '正常' : '异常'}</strong>
                {' · '}环境: {health.env}
                {' · '}版本: {health.version}
              </p>
              <p className="uptime">运行时间: {health.uptime}</p>
            </div>
          </div>
        </section>
      )}

      {/* Service Checks */}
      {health && (
        <section className="checks-section">
          <h3>服务状态</h3>
          <div className="checks-grid">
            <div className={`check-card ${getStatusColor(health.checks.database.status)}`}>
              <div className="check-icon">🗄️</div>
              <div className="check-name">数据库</div>
              <div className="check-status">{health.checks.database.status === 'healthy' ? '正常' : '异常'}</div>
              {health.checks.database.error && (
                <div className="check-error">{health.checks.database.error}</div>
              )}
            </div>
            <div className={`check-card ${getStatusColor(health.checks.redis.status)}`}>
              <div className="check-icon">⚡</div>
              <div className="check-name">Redis</div>
              <div className="check-status">{health.checks.redis.status === 'healthy' ? '正常' : '异常'}</div>
              {health.checks.redis.error && (
                <div className="check-error">{health.checks.redis.error}</div>
              )}
            </div>
          </div>
        </section>
      )}

      {/* Metrics */}
      {metrics && (
        <>
          <section className="metrics-section">
            <h3>数据库连接池</h3>
            <div className="metrics-grid">
              <div className="metric-card">
                <div className="metric-value">{metrics.database_pool.pool_size ?? '—'}</div>
                <div className="metric-label">池大小</div>
              </div>
              <div className="metric-card">
                <div className="metric-value">{metrics.database_pool.checked_in ?? '—'}</div>
                <div className="metric-label">空闲连接</div>
              </div>
              <div className="metric-card">
                <div className="metric-value">{metrics.database_pool.checked_out ?? '—'}</div>
                <div className="metric-label">使用中</div>
              </div>
              <div className="metric-card">
                <div className="metric-value">{metrics.database_pool.overflow ?? '—'}</div>
                <div className="metric-label">溢出</div>
              </div>
            </div>
          </section>

          <section className="metrics-section">
            <h3>WebSocket</h3>
            <div className="metrics-grid">
              <div className="metric-card">
                <div className="metric-value">{metrics.websocket.active_rooms}</div>
                <div className="metric-label">活跃房间</div>
              </div>
              <div className="metric-card">
                <div className="metric-value">{metrics.websocket.total_connections}</div>
                <div className="metric-label">总连接数</div>
              </div>
              <div className="metric-card">
                <div className={`metric-value ${metrics.redis_connected ? 'text-green' : 'text-red'}`}>
                  {metrics.redis_connected ? '已连接' : '断开'}
                </div>
                <div className="metric-label">Redis 状态</div>
              </div>
            </div>

            {/* WebSocket rooms detail */}
            {Object.keys(metrics.websocket.rooms).length > 0 && (
              <div className="rooms-detail">
                <h4>房间详情</h4>
                <table className="rooms-table">
                  <thead>
                    <tr>
                      <th>房间 ID</th>
                      <th>连接数</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(metrics.websocket.rooms).map(([room, count]) => (
                      <tr key={room}>
                        <td><code>{room}</code></td>
                        <td>{count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}

      {health && (
        <div className="last-updated">
          最后更新: {new Date(health.timestamp).toLocaleString('zh-CN')}
        </div>
      )}
    </div>
  )
}
