import { useAuthStore } from '@/store/auth'
import { useNavigate } from 'react-router-dom'

export default function IDELayout() {
  const username = useAuthStore((s) => s.username)
  const logout = useAuthStore((s) => s.logout)
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="ide-layout">
      {/* Header */}
      <header className="ide-header">
        <div className="ide-header-left">
          <span className="ide-logo">AI-Collab-OS</span>
        </div>
        <div className="ide-header-center">
          <span className="ide-project-name">未选择项目</span>
        </div>
        <div className="ide-header-right">
          <span className="ide-username">{username}</span>
          <button className="btn-sm" onClick={handleLogout}>退出</button>
        </div>
      </header>

      {/* Main Content */}
      <div className="ide-body">
        {/* Sidebar */}
        <aside className="ide-sidebar">
          <nav className="ide-nav">
            <button className="ide-nav-item active">项目</button>
            <button className="ide-nav-item">Agent</button>
            <button className="ide-nav-item">工作流</button>
            <button className="ide-nav-item">文件</button>
            <button className="ide-nav-item">设置</button>
          </nav>
        </aside>

        {/* Center Panel */}
        <main className="ide-main">
          <div className="ide-welcome">
            <h2>欢迎使用 AI-Collab-OS</h2>
            <p>选择或创建一个项目开始协作开发</p>
            <div className="ide-quick-actions">
              <button className="btn-primary">新建项目</button>
              <button className="btn-secondary">导入项目</button>
            </div>
          </div>
        </main>

        {/* Right Panel - Agent Communication */}
        <aside className="ide-right-panel">
          <div className="ide-panel-header">
            <span>Agent 通信</span>
          </div>
          <div className="ide-panel-body">
            <p className="ide-placeholder">启动工作流后，Agent 间的通信将在此显示</p>
          </div>
        </aside>
      </div>

      {/* Status Bar */}
      <footer className="ide-statusbar">
        <span>就绪</span>
        <span>Agent: 0 活跃</span>
        <span>Token: 0</span>
      </footer>
    </div>
  )
}
