import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'
import { authApi } from '@/api/auth'

export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const setAuth = useAuthStore((s) => s.setAuth)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const res = isRegister
        ? await authApi.register({ username, password, email: email || undefined })
        : await authApi.login({ username, password })

      const data = res.data
      setAuth({
        token: data.access_token,
        userId: data.user_id,
        username: data.username,
        role: data.role,
      })
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail || '操作失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <h1 className="login-title">AI-Collab-OS</h1>
        <p className="login-subtitle">多 Agent 协作开发平台</p>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="username">用户名</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="输入用户名"
              required
              minLength={3}
            />
          </div>

          {isRegister && (
            <div className="form-group">
              <label htmlFor="email">邮箱（可选）</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="输入邮箱"
              />
            </div>
          )}

          <div className="form-group">
            <label htmlFor="password">密码</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="输入密码"
              required
              minLength={6}
            />
          </div>

          {error && <div className="form-error">{error}</div>}

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? '处理中...' : isRegister ? '注册' : '登录'}
          </button>
        </form>

        <div className="login-switch">
          <span>{isRegister ? '已有账号？' : '没有账号？'}</span>
          <button
            type="button"
            className="btn-link"
            onClick={() => setIsRegister(!isRegister)}
          >
            {isRegister ? '去登录' : '去注册'}
          </button>
        </div>
      </div>
    </div>
  )
}
