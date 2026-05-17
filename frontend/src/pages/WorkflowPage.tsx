import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  reconnectEdge,
  useNodesState,
  useEdgesState,
  type Connection,
  type Node,
  type Edge,
  type NodeDragHandler,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import AgentNode from '@/components/workflow/AgentNode'
import { useAgentStore } from '@/store/agent'
import { workflowApi, type DagConfig, type DagNode, type WorkflowListItem } from '@/api/workflows'

const nodeTypes = { agent: AgentNode }

const defaultEdgeOptions = {
  animated: true,
  style: { stroke: 'var(--accent)', strokeWidth: 2 },
}

export default function WorkflowPage() {
  const { id: projectId } = useParams<{ id: string }>()
  const { agents, fetchAgents } = useAgentStore()
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const [workflowName, setWorkflowName] = useState('')
  const [taskDesc, setTaskDesc] = useState('')
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(true)
  const [workflowId, setWorkflowId] = useState<string | null>(null)
  const [workflows, setWorkflows] = useState<WorkflowListItem[]>([])
  const autoSaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const nodesRef = useRef(nodes)
  const edgesRef = useRef(edges)
  const workflowIdRef = useRef(workflowId)

  nodesRef.current = nodes
  edgesRef.current = edges
  workflowIdRef.current = workflowId

  useEffect(() => {
    if (!projectId) return
    fetchAgents(projectId)
    loadWorkflows(projectId)
  }, [projectId, fetchAgents])

  const buildDagConfig = useCallback((currentNodes: Node[], currentEdges: Edge[]): DagConfig => ({
    nodes: currentNodes.map((n): DagNode => ({
      id: n.id,
      agent_id: (n.data as Record<string, unknown>).agentId as string,
      step_type: (n.data as Record<string, unknown>).stepType as DagNode['step_type'],
      label: (n.data as Record<string, unknown>).label as string,
      position: { x: n.position.x, y: n.position.y },
    })),
    edges: currentEdges.map((e) => ({
      from: e.source,
      to: e.target,
    })),
  }), [])

  const autoSave = useCallback(() => {
    if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current)
    autoSaveTimer.current = setTimeout(async () => {
      const wfId = workflowIdRef.current
      const currentNodes = nodesRef.current
      const currentEdges = edgesRef.current
      if (!wfId || currentNodes.length === 0) return
      try {
        await workflowApi.update(wfId, {
          dag_config: buildDagConfig(currentNodes, currentEdges),
        })
      } catch (e) {
        console.error('Auto-save failed:', e)
      }
    }, 800)
  }, [buildDagConfig])

  const loadWorkflows = async (pid: string) => {
    setLoading(true)
    try {
      const res = await workflowApi.list(pid)
      setWorkflows(res.data)
      if (res.data.length > 0) {
        await loadWorkflow(res.data[0].id)
      }
    } catch (e) {
      console.error('Load workflows failed:', e)
    } finally {
      setLoading(false)
    }
  }

  const loadWorkflow = async (wfId: string) => {
    try {
      const res = await workflowApi.get(wfId)
      setWorkflowId(res.data.id)
      setWorkflowName(res.data.name || '')

      const { nodes: dagNodes, edges: dagEdges } = res.data.dag_config
      const flowNodes: Node[] = dagNodes.map((n, i) => ({
        id: n.id,
        type: 'agent',
        position: n.position || { x: 180 + i * 240, y: 100 + (i % 2) * 130 },
        data: {
          label: n.label,
          icon: getStepIcon(n.step_type),
          agentId: n.agent_id,
          stepType: n.step_type,
          status: 'pending',
          onDelete: handleDeleteNode,
        },
      }))
      const flowEdges: Edge[] = dagEdges.map((e, i) => ({
        id: `edge_${i}_${e.from}_${e.to}`,
        source: e.from,
        target: e.to,
        animated: true,
      }))
      setNodes(flowNodes)
      setEdges(flowEdges)
    } catch (e) {
      console.error('Load workflow failed:', e)
    }
  }

  const getStepIcon = (stepType: string) => {
    const icons: Record<string, string> = { execute: '🤖', review: '🔍', discuss: '💬', assign: '📋' }
    return icons[stepType] || '🤖'
  }

  const handleDeleteNode = useCallback((nodeId: string) => {
    setNodes((nds) => nds.filter((n) => n.id !== nodeId))
    setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId))
    setTimeout(() => autoSave(), 100)
  }, [setNodes, setEdges, autoSave])

  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds: Edge[]) => addEdge({ ...params, animated: true }, eds))
      setTimeout(() => autoSave(), 100)
    },
    [setEdges, autoSave]
  )

  const onReconnect = useCallback(
    (oldEdge: Edge, newConnection: Connection) => {
      setEdges((eds) => reconnectEdge(oldEdge, newConnection, eds))
      setTimeout(() => autoSave(), 100)
    },
    [setEdges, autoSave]
  )

  const onNodeDragStop: NodeDragHandler = useCallback(() => {
    autoSave()
  }, [autoSave])

  const onEdgesDelete = useCallback(() => {
    setTimeout(() => autoSave(), 100)
  }, [autoSave])

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
        onDelete: handleDeleteNode,
      },
    }
    setNodes((nds: Node[]) => [...nds, newNode])
    setTimeout(() => autoSave(), 100)
  }

  const handleSave = async () => {
    if (!projectId || nodes.length === 0) return
    setSaving(true)
    try {
      if (workflowId) {
        await workflowApi.update(workflowId, {
          name: workflowName || '自定义工作流',
          dag_config: buildDagConfig(nodes, edges),
        })
      } else {
        const res = await workflowApi.create(projectId, {
          name: workflowName || '自定义工作流',
          type: 'custom',
          dag_config: buildDagConfig(nodes, edges),
          mode: 'manual',
        })
        setWorkflowId(res.data.id)
        setWorkflows((prev) => [...prev, { id: res.data.id, name: res.data.name, type: res.data.type, status: res.data.status, mode: res.data.mode, created_at: res.data.created_at }])
      }
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

  const handleWorkflowSwitch = async (wfId: string) => {
    await loadWorkflow(wfId)
  }

  if (loading) {
    return <div className="workflow-page"><div className="workflow-loading">加载工作流...</div></div>
  }

  return (
    <div className="workflow-page">
      <header className="workflow-header">
        <h1>⚡ 工作流编排</h1>
        <div className="workflow-actions">
          {workflows.length > 1 && (
            <select
              className="workflow-select"
              value={workflowId || ''}
              onChange={(e) => handleWorkflowSwitch(e.target.value)}
            >
              {workflows.map((wf) => (
                <option key={wf.id} value={wf.id}>{wf.name || '未命名'}</option>
              ))}
            </select>
          )}
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
        <aside className="agent-palette">
          <h3>Agent 面板</h3>
          <p className="palette-hint">点击添加到画布，Delete 键删除连线</p>
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

        <div className="workflow-canvas">
          {nodes.length === 0 && (
            <div className="canvas-hint">从左侧面板添加 Agent 节点，拖拽连线构建工作流</div>
          )}
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onReconnect={onReconnect}
            onNodeDragStop={onNodeDragStop}
            onEdgesDelete={onEdgesDelete}
            nodeTypes={nodeTypes}
            defaultEdgeOptions={defaultEdgeOptions}
            deleteKeyCode="Delete"
            fitView
            proOptions={{ hideAttribution: true }}
          >
            <Background color="rgba(137, 180, 250, 0.08)" gap={24} />
            <Controls />
            <MiniMap
              nodeColor={() => 'var(--accent)'}
              maskColor="rgba(0,0,0,0.6)"
            />
          </ReactFlow>
        </div>
      </div>
    </div>
  )
}
