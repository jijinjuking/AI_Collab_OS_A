import { Handle, Position, type NodeProps } from '@xyflow/react'

interface AgentNodeData {
  label: string
  icon: string
  agentId: string
  stepType: string
  status: string
}

export default function AgentNode({ data }: NodeProps) {
  const { label, icon, stepType, status } = data as unknown as AgentNodeData

  const stepColors: Record<string, string> = {
    execute: 'var(--accent)',
    review: 'var(--warning)',
    discuss: 'var(--success)',
    assign: '#cba6f7',
  }

  const stepLabels: Record<string, string> = {
    execute: '执行',
    review: '审查',
    discuss: '讨论',
    assign: '分配',
  }

  return (
    <div className="agent-node" style={{ borderColor: stepColors[stepType] || 'var(--border)' }}>
      <Handle type="target" position={Position.Left} />
      <div className="agent-node-header">
        <span className="agent-node-icon">{icon}</span>
        <span className="agent-node-label">{label as string}</span>
      </div>
      <div className="agent-node-footer">
        <span className="agent-node-type" style={{ color: stepColors[stepType] }}>
          {stepLabels[stepType] || stepType}
        </span>
        {status === 'working' && <span className="agent-node-pulse" />}
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  )
}
