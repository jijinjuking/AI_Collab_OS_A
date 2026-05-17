import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useProjectStore } from '@/store/project'

export default function ProjectListPage() {
  const { projects, loading, error, fetchProjects, createProject, deleteProject } = useProjectStore()
  const navigate = useNavigate()
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [newDesc, setNewDesc] = useState('')

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  const handleCreate = async () => {
    if (!newName.trim()) return
    try {
      const project = await createProject({ name: newName.trim(), description: newDesc.trim() || undefined })
      setShowCreate(false)
      setNewName('')
      setNewDesc('')
      navigate(`/project/${project.id}`)
    } catch (e) {
      // error handled by store
    }
  }

  const statusLabel: Record<string, string> = {
    draft: '草稿',
    active: '进行中',
    paused: '已暂停',
    completed: '已完成',
    archived: '已归档',
  }

  const statusColor: Record<string, string> = {
    draft: 'var(--text-secondary)',
    active: 'var(--accent)',
    paused: 'var(--warning)',
    completed: 'var(--success)',
    archived: 'var(--text-secondary)',
  }

  return (
    <div className="project-list-page">
      <header className="page-header">
        <h1>我的项目</h1>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>
          + 新建项目
        </button>
      </header>

      {error && <div className="error-banner">{error}</div>}

      {showCreate && (
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>新建项目</h2>
            <div className="form-group">
              <label>项目名称</label>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="输入项目名称"
                autoFocus
              />
            </div>
            <div className="form-group">
              <label>项目描述（可选）</label>
              <textarea
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                placeholder="简要描述项目目标"
                rows={3}
              />
            </div>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowCreate(false)}>取消</button>
              <button className="btn-primary" onClick={handleCreate} disabled={!newName.trim()}>创建</button>
            </div>
          </div>
        </div>
      )}

      {loading && projects.length === 0 ? (
        <div className="loading">加载中...</div>
      ) : projects.length === 0 ? (
        <div className="empty-state">
          <p>还没有项目，点击上方按钮创建第一个项目</p>
        </div>
      ) : (
        <div className="project-grid">
          {projects.map((p) => (
            <div key={p.id} className="project-card" onClick={() => navigate(`/project/${p.id}`)}>
              <div className="project-card-header">
                <h3>{p.name}</h3>
                <span className="status-badge" style={{ color: statusColor[p.status] }}>
                  {statusLabel[p.status] || p.status}
                </span>
              </div>
              {p.description && <p className="project-desc">{p.description}</p>}
              <div className="project-card-footer">
                <span className="date">{new Date(p.created_at).toLocaleDateString('zh-CN')}</span>
                <button
                  className="btn-danger-sm"
                  onClick={(e) => {
                    e.stopPropagation()
                    if (confirm('确定删除此项目？')) deleteProject(p.id)
                  }}
                >
                  删除
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
