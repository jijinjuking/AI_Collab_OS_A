import { useCallback, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { useWebSocket, type WSMessage } from '@/hooks/useWebSocket'
import { useMessageStore, type ChatMessage } from '@/store/message'

export default function MessagePanel() {
  const { id: projectId } = useParams<{ id: string }>()
  const { messages, handleWSMessage, clearMessages } = useMessageStore()
  const bottomRef = useRef<HTMLDivElement>(null)

  const onMessage = useCallback((msg: WSMessage) => {
    handleWSMessage(msg)
  }, [handleWSMessage])

  useWebSocket(projectId, onMessage)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length])

  // Clear messages when switching projects
  useEffect(() => {
    clearMessages()
  }, [projectId, clearMessages])

  const getMessageIcon = (msg: ChatMessage) => {
    switch (msg.type) {
      case 'agent_message': return '🤖'
      case 'workflow_event': return '⚡'
      default: return '📢'
    }
  }

  const getMessageTypeLabel = (msg: ChatMessage) => {
    const mt = msg.metadata?.messageType as string
    switch (mt) {
      case 'execute': return '执行'
      case 'review': return '审查'
      case 'discuss': return '讨论'
      case 'assign': return '分配'
      default: return msg.type === 'workflow_event' ? '工作流' : '消息'
    }
  }

  const getVerdictBadge = (msg: ChatMessage) => {
    const verdict = msg.metadata?.verdict as string
    if (!verdict) return null
    const cls = verdict === 'pass' ? 'verdict-pass' : 'verdict-revise'
    const label = verdict === 'pass' ? '✓ 通过' : '↻ 修改'
    return <span className={`verdict-badge ${cls}`}>{label}</span>
  }

  return (
    <div className="message-panel">
      <header className="message-panel-header">
        <h2>💬 实时消息</h2>
        <span className="msg-count">{messages.length} 条消息</span>
      </header>

      <div className="message-list">
        {messages.length === 0 ? (
          <div className="empty-messages">
            <p>等待 Agent 消息...</p>
            <p className="hint">启动工作流后，Agent 间的对话将实时显示在这里</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`message-item message-${msg.type}`}>
              <div className="message-header">
                <span className="message-icon">{getMessageIcon(msg)}</span>
                <span className="message-from">
                  {msg.fromAgentName || '系统'}
                </span>
                <span className="message-type-label">{getMessageTypeLabel(msg)}</span>
                {getVerdictBadge(msg)}
                <span className="message-time">
                  {new Date(msg.timestamp).toLocaleTimeString('zh-CN')}
                </span>
              </div>
              <div className="message-content">
                {msg.content}
              </div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
