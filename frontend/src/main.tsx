import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/global.css'
import './styles/pages.css'
import './styles/agents.css'
import './styles/messages.css'
import './styles/workflow.css'
import './styles/toast.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
