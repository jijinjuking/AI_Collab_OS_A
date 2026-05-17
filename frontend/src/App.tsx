import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/auth'
import LoginPage from './pages/LoginPage'
import ProjectListPage from './pages/ProjectListPage'
import ProjectDetailPage from './pages/ProjectDetailPage'
import AgentConfigPage from './pages/AgentConfigPage'
import ChatPage from './pages/ChatPage'
import WorkflowPage from './pages/WorkflowPage'
import ApiKeysPage from './pages/ApiKeysPage'
import DashboardPage from './pages/DashboardPage'
import IDELayout from './components/layout/IDELayout'
import ToastContainer from './components/ToastContainer'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
      <ToastContainer />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <Routes>
                <Route path="/projects" element={<ProjectListPage />} />
                <Route path="/project/:id" element={<ProjectDetailPage />} />
                <Route path="/project/:id/agents" element={<AgentConfigPage />} />
                <Route path="/project/:id/chat" element={<ChatPage />} />
                <Route path="/project/:id/workflow" element={<WorkflowPage />} />
                <Route path="/project/:id/*" element={<IDELayout />} />
                <Route path="/settings/api-keys" element={<ApiKeysPage />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="*" element={<Navigate to="/projects" replace />} />
              </Routes>
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}
