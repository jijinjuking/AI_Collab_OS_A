import { useEffect, useState } from 'react'
import { useApiKeyStore } from '@/store/apiKey'
import '@/styles/apikeys.css'

export default function ApiKeysPage() {
  const { keys, loading, newlyCreated, fetchKeys, createKey, revokeKey, deleteKey, clearNewlyCreated } =
    useApiKeyStore()

  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [scopes, setScopes] = useState('read,write')
  const [expiresIn, setExpiresIn] = useState('')
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    fetchKeys()
  }, [fetchKeys])

  const handleCreate = async () => {
    if (!name.trim()) return
    let expiresAt: string | null = null
    if (expiresIn) {
      const days = parseInt(expiresIn)
      if (days > 0) {
        const d = new Date()
        d.setDate(d.getDate() + days)
        expiresAt = d.toISOString()
      }
    }
    await createKey(name.trim(), scopes, expiresAt)
    setName('')
    setScopes('read,write')
    setExpiresIn('')
    setShowCreate(false)
  }

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—'
    return new Date(dateStr).toLocaleString('zh-CN')
  }

  return (
    <div className="apikeys-page">
      <div className="apikeys-header">
        <h1>API Key 管理</h1>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>
          + 创建 API Key
        </button>
      </div>

      {/* Newly created key alert */}
      {newlyCreated && (
        <div className="key-created-alert">
          <div className="alert-header">
            <span className="alert-icon">⚠️</span>
            <strong>请立即复制保存此 Key，关闭后将无法再次查看</strong>
          </div>
          <div className="raw-key-display">
            <code>{newlyCreated.raw_key}</code>
            <button
              className="btn-copy"
              onClick={() => handleCopy(newlyCreated.raw_key)}
            >
              {copied ? '✓ 已复制' : '复制'}
            </button>
          </div>
          <button className="btn-dismiss" onClick={clearNewlyCreated}>
            我已保存，关闭提示
          </button>
        </div>
      )}

      {/* Create form modal */}
      {showCreate && (
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>创建 API Key</h2>
            <div className="form-group">
              <label>名称</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="例如: 生产环境、CI/CD"
                autoFocus
              />
            </div>
            <div className="form-group">
              <label>权限范围</label>
              <select value={scopes} onChange={(e) => setScopes(e.target.value)}>
                <option value="read">只读 (read)</option>
                <option value="read,write">读写 (read,write)</option>
                <option value="read,write,admin">管理员 (read,write,admin)</option>
              </select>
            </div>
            <div className="form-group">
              <label>有效期（天）</label>
              <input
                type="number"
                value={expiresIn}
                onChange={(e) => setExpiresIn(e.target.value)}
                placeholder="留空表示永不过期"
                min="1"
              />
            </div>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowCreate(false)}>
                取消
              </button>
              <button className="btn-primary" onClick={handleCreate} disabled={!name.trim()}>
                创建
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Keys table */}
      {loading ? (
        <div className="loading">加载中...</div>
      ) : keys.length === 0 ? (
        <div className="empty-state">
          <p>暂无 API Key</p>
          <p className="hint">创建一个 API Key 来通过接口访问平台</p>
        </div>
      ) : (
        <div className="keys-table-wrapper">
          <table className="keys-table">
            <thead>
              <tr>
                <th>名称</th>
                <th>Key 前缀</th>
                <th>权限</th>
                <th>状态</th>
                <th>过期时间</th>
                <th>最后使用</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {keys.map((key) => (
                <tr key={key.id} className={!key.is_active ? 'revoked' : ''}>
                  <td className="key-name">{key.name}</td>
                  <td><code>{key.key_prefix}...</code></td>
                  <td>
                    <span className="scope-badge">{key.scopes}</span>
                  </td>
                  <td>
                    <span className={`status-badge ${key.is_active ? 'active' : 'inactive'}`}>
                      {key.is_active ? '活跃' : '已撤销'}
                    </span>
                  </td>
                  <td>{formatDate(key.expires_at)}</td>
                  <td>{formatDate(key.last_used_at)}</td>
                  <td>{formatDate(key.created_at)}</td>
                  <td className="actions">
                    {key.is_active && (
                      <button
                        className="btn-warn"
                        onClick={() => revokeKey(key.id)}
                      >
                        撤销
                      </button>
                    )}
                    <button
                      className="btn-danger"
                      onClick={() => {
                        if (confirm('确定要永久删除此 API Key？')) {
                          deleteKey(key.id)
                        }
                      }}
                    >
                      删除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
