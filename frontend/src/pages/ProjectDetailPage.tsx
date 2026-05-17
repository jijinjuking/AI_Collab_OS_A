import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useProjectStore } from '@/store/project'

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { currentProject, loading, error, fetchProject } = useProjectStore()

  useEffect(() => {
    if (id) fetchProject(id)
  }, [id, fetchProject])

  if (loading) return <div className="loading">加载中...</div>
  if (error) return <div className="error-banner">{error}</div>
  if (!currentProject) return <div className="loading">项目不存在</div>

  return (
    <div className="project-detail-page">
      <header className="page-header">
        <button className="btn-back" onClick={() => navigate('/projects')}>← 返回</button>
        <h1>{currentProject.name}</h1>
        <span className="status-badge">{currentProject.status}</span>
      </header>

      <div className="project-detail-grid">
        {/* Left: Project Info */}
        <section className="detail-section">
          <h2>项目信息</h2>
          {currentProject.description && (
            <div className="info-row">
              <label>描述</label>
              <p>{currentProject.description}</p>
            </div>
          )}
          {currentProject.plan && (
            <div className="info-row">
              <label>计划</label>
              <pre className="plan-content">{currentProject.plan}</pre>
            </div>
          )}
          <div className="info-row">
            <label>创建时间</label>
            <p>{new Date(currentProject.created_at).toLocaleString('zh-CN')}</p>
          </div>
        </section>

        {/* Right: Quick Actions */}
        <section className="detail-section">
          <h2>快捷操作</h2>
          <div className="action-buttons">
            <button className="btn-primary" onClick={() => navigate(`/project/${id}/agents`)}>
              🤖 配置 Agent 团队
            </button>
            <button className="btn-primary" onClick={() => navigate(`/project/${id}/workflow`)}>
              ⚡ 工作流编排
            </button>
            <button className="btn-primary" onClick={() => navigate(`/project/${id}/chat`)}>
              💬 实时消息
            </button>
          </div>
        </section>
      </div>
    </div>
  )
}
