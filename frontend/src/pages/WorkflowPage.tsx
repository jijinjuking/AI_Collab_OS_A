import { useCallback, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  type Connection,
  type Node,
  type Edge,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import AgentNode from '@/components/workflow/AgentNode'
import { useAgentStore } from '@/store/agent'
import { workflowApi, type DagConfig, type DagNode } from '@/api/workflows'

const nodeTypes = { agent: AgentNode }

const defaultEdgeOptions = {
  animated: true,
  style: { stroke: 'var(--accent)', strokeWidth: 2 },
}

export default function WorkflowPage() {
  const { id: projectId } = useParams<{ id: string }>()
  const { agents } = useAgentStore()
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const [workflowName, setWorkflowName] = useState('')
  const [taskDesc, setTaskDesc] = useState('')
  const [saving, setSaving] = useState(false)
  const [workflowId, setWorkflowId] = useState<string | null>(null)

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds: Edge[]) => addEdge({ ...params, animated: true }, eds)),
    [setEdges]
  )

  // Add agent as a node to the canvas
  const addAgentNode = (agentId: string, roleName: string, icon: string, stepType: string) => {
    const id = `node_${Date.now()}`
    const newNode: Node = {
      id,
      type: 'agent',
      position: { x: 150 + nodes.length * 220, y: 100 + (nodes.length % 2) * 120 },
      data: {
        label: roleName,
        icon,
        agentId,
        stepType,
        status: 'pending',
      },
    }
    setNodes((nds: Node[]) => [...nds, newNode])
  }

  // Convert React Flow state to DAG config
  const toDagConfig = (): DagConfig => ({
    nodes: nodes.map((n): DagNode => ({
      id: n.id,
      agent_id: (n.data as Record<string, unknown>).agentId as string,
      step_type: (n.data as Record<string, unknown>).stepType as DagNode['step_type'],
      label: (n.data as Record<string, unknown>).label as string,
    })),
    edges: edges.map((e) => ({
      from: e.source,
      to: e.target,
    })),
  })

  const handleSave = async () => {
    if (!projectId || nodes.length === 0) return
    setSaving(true)
    try {
      const res = await workflowApi.create(projectId, {
        name: workflowName || '自定义工作流',
        type: 'custom',
        dag_config: toDagConfig(),
        mode: 'manual',
      })
      setWorkflowId(res.data.id)
    } catch (e) {
      console.error('Save workflow failed:', e)
    } finally {
      setSaving(false)
    }
  }

  const handleStart = async () => {
    if (!workflowId || !taskDesc.trim()) return
    try {
      await workflowApi.start(workflowId, { task_description: taskDesc })
    } catch (e) {
      console.error('Start workflow failed:', e)
    }
  }

  return (
    <div className="workflow-page">
      <header className="workflow-header">
        <h1>⚡ 工作流编排</h1>
        <div className="workflow-actions">
          <input
            className="workflow-name-input"
            placeholder="工作流名称"
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
          />
          <button className="btn-primary" onClick={handleSave} disabled={saving || nodes.length === 0}>
            {saving ? '保存中...' : '💾 保存'}
          </button>
          {workflowId && (
            <>
              <input
                className="task-desc-input"
                placeholder="输入任务描述..."
                value={taskDesc}
                onChange={(e) => setTaskDesc(e.target.value)}
              />
              <button className="btn-primary" onClick={handleStart} disabled={!taskDesc.trim()}>
                ▶ 启动
              </button>
            </>
          )}
        </div>
      </header>

      <div className="workflow-body">
        {/* Agent palette */}
        <aside className="agent-palette">
          <h3>Agent 面板</h3>
          <p className="palette-hint">点击添加到画布</p>
          {agents.map((agent) => (
            <div
              key={agent.id}
              className="palette-item"
              onClick={() => addAgentNode(agent.id, agent.instance_name, '🤖', 'execute')}
            >
              <span className="palette-icon">🤖</span>
              <span className="palette-name">{agent.instance_name}</span>
              <span className="palette-role">{agent.role_template_id.slice(0, 8)}</span>
            </div>
          ))}
          <hr className="palette-divider" />
          <h4>步骤类型</h4>
          <div className="step-type-buttons">
            <button onClick={() => addAgentNode('', '审查节点', '🔍', 'review')}>🔍 审查</button>
            <button onClick={() => addAgentNode('', '讨论节点', '💬', 'discuss')}>💬 讨论</button>
            <button onClick={() => addAgentNode('', '分配节点', '📋', 'assign')}>📋 分配</button>
          </div>
        </aside>

        {/* React Flow canvas */}
        <div className="workflow-canvas">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            defaultEdgeOptions={defaultEdgeOptions}
            fitView
            proOptions={{ hideAttribution: true }}
          >
            <Background color="var(--border)" gap={20} />
            <Controls />
            <MiniMap
              nodeColor={() => 'var(--accent)'}
              maskColor="rgba(0,0,0,0.5)"
            />
          </ReactFlow>
        </div>
      </div>
    </div>
  )
}
