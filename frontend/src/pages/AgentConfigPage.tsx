import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useAgentStore } from '@/store/agent'
import type { CreateAgentPayload, UpdateAgentPayload } from '@/api/agents'

const MODEL_OPTIONS = [
  { value: 'gpt-4o', label: 'GPT-4o' },
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
  { value: 'claude-3-5-sonnet', label: 'Claude 3.5 Sonnet' },
  { value: 'claude-3-5-haiku', label: 'Claude 3.5 Haiku' },
  { value: 'deepseek-chat', label: 'DeepSeek V3' },
  { value: 'deepseek-reasoner', label: 'DeepSeek R1' },
]

export default function AgentConfigPage() {
  const { id: projectId } = useParams<{ id: string }>()
  const { roles, agents, loading, error, fetchRoles, fetchAgents, createAgent, updateAgent, deleteAgent } = useAgentStore()
  const [showAdd, setShowAdd] = useState(false)
  const [selectedRoleId, setSelectedRoleId] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState<UpdateAgentPayload>({})

  useEffect(() => {
    fetchRoles()
    if (projectId) fetchAgents(projectId)
  }, [projectId, fetchRoles, fetchAgents])

  const handleAdd = async () => {
    if (!projectId || !selectedRoleId) return
    const role = roles.find((r) => r.id === selectedRoleId)
    const payload: CreateAgentPayload = {
      role_template_id: selectedRoleId,
      instance_name: role?.name || '新 Agent',
    }
    await createAgent(projectId, payload)
    setShowAdd(false)
    setSelectedRoleId('')
  }

  const handleUpdate = async (agentId: string) => {
    await updateAgent(agentId, editForm)
    setEditingId(null)
    setEditForm({})
  }

  const handleDelete = async (agentId: string, name: string) => {
    if (confirm(`确定删除 Agent "${name}"？`)) {
      await deleteAgent(agentId)
    }
  }

  const getRoleInfo = (roleTemplateId: string) => roles.find((r) => r.id === roleTemplateId)

  return (
    <div className="agent-config-page">
      <header className="page-header">
        <h1>🤖 Agent 团队配置</h1>
        <button className="btn-primary" onClick={() => setShowAdd(true)}>
          + 添加 Agent
        </button>
      </header>

      {error && <div className="error-banner">{error}</div>}

      {/* Add Agent Modal */}
      {showAdd && (
        <div className="modal-overlay" onClick={() => setShowAdd(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>添加 Agent</h2>
            <p className="modal-desc">选择一个角色模板来创建 Agent 实例</p>
            <div className="role-grid">
              {roles.map((role) => (
                <div
                  key={role.id}
                  className={`role-card ${selectedRoleId === role.id ? 'selected' : ''}`}
                  onClick={() => setSelectedRoleId(role.id)}
                >
                  <span className="role-icon">{role.icon || '🤖'}</span>
                  <span className="role-name">{role.name}</span>
                  {role.skills && (
                    <div className="role-skills">
                      {role.skills.slice(0, 3).map((s) => (
                        <span key={s} className="skill-tag">{s}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowAdd(false)}>取消</button>
              <button className="btn-primary" onClick={handleAdd} disabled={!selectedRoleId}>
                添加
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Agent List */}
      {loading ? (
        <div className="loading">加载中...</div>
      ) : agents.length === 0 ? (
        <div className="empty-state">
          <p>还没有 Agent，点击上方按钮添加团队成员</p>
        </div>
      ) : (
        <div className="agent-list">
          {agents.map((agent) => {
            const role = getRoleInfo(agent.role_template_id)
            const isEditing = editingId === agent.id
            return (
              <div key={agent.id} className="agent-card">
                <div className="agent-card-header">
                  <span className="agent-icon">{role?.icon || '🤖'}</span>
                  <div className="agent-info">
                    {isEditing ? (
                      <input
                        className="edit-input"
                        value={editForm.instance_name || agent.instance_name}
                        onChange={(e) => setEditForm({ ...editForm, instance_name: e.target.value })}
                      />
                    ) : (
                      <h3>{agent.instance_name}</h3>
                    )}
                    <span className="agent-role">{role?.name || agent.role_template_id}</span>
                  </div>
                  <span className={`agent-status status-${agent.status}`}>
                    {agent.status === 'idle' ? '空闲' : agent.status === 'working' ? '工作中' : agent.status}
                  </span>
                </div>

                <div className="agent-config-row">
                  <label>模型</label>
                  {isEditing ? (
                    <select
                      value={editForm.model || agent.model || ''}
                      onChange={(e) => setEditForm({ ...editForm, model: e.target.value || undefined })}
                    >
                      <option value="">默认 ({role?.default_model || 'gpt-4o'})</option>
                      {MODEL_OPTIONS.map((m) => (
                        <option key={m.value} value={m.value}>{m.label}</option>
                      ))}
                    </select>
                  ) : (
                    <span>{agent.model || role?.default_model || 'gpt-4o'}</span>
                  )}
                </div>

                <div className="agent-config-row">
                  <label>Provider</label>
                  <span>{agent.provider || '默认'}</span>
                </div>

                <div className="agent-config-row">
                  <label>Token 用量</label>
                  <span>{agent.token_used.toLocaleString()}</span>
                </div>

                <div className="agent-card-actions">
                  {isEditing ? (
                    <>
                      <button className="btn-secondary" onClick={() => { setEditingId(null); setEditForm({}) }}>取消</button>
                      <button className="btn-primary" onClick={() => handleUpdate(agent.id)}>保存</button>
                    </>
                  ) : (
                    <>
                      <button className="btn-secondary" onClick={() => { setEditingId(agent.id); setEditForm({}) }}>编辑</button>
                      <button className="btn-danger-sm" onClick={() => handleDelete(agent.id, agent.instance_name)}>删除</button>
                    </>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
