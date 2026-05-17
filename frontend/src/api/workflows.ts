import api from './client'

export interface WorkflowListItem {
  id: string
  name: string | null
  type: string
  status: string
  mode: string
  created_at: string
}

export interface Workflow {
  id: string
  project_id: string
  name: string | null
  type: string
  status: string
  dag_config: DagConfig
  current_step_id: string | null
  mode: string
  max_review_rounds: number
  started_at: string | null
  completed_at: string | null
  created_at: string
  updated_at: string
}

export interface DagNode {
  id: string
  agent_id: string
  step_type: 'execute' | 'review' | 'discuss' | 'assign'
  label: string
  review_targets?: string[]
  assign_to?: string[]
  discuss_with?: string
}

export interface DagEdge {
  from: string
  to: string
}

export interface DagConfig {
  nodes: DagNode[]
  edges: DagEdge[]
}

export interface CreateWorkflowPayload {
  name?: string
  type: 'full' | 'frontend' | 'backend' | 'custom'
  dag_config: DagConfig
  mode?: 'auto' | 'manual'
  max_review_rounds?: number
}

export interface StartWorkflowPayload {
  task_description: string
}

export const workflowApi = {
  list: (projectId: string) => api.get<WorkflowListItem[]>(`/workflows/project/${projectId}`),
  get: (workflowId: string) => api.get<Workflow>(`/workflows/${workflowId}`),
  create: (projectId: string, data: CreateWorkflowPayload) =>
    api.post<Workflow>(`/workflows/project/${projectId}`, data),
  start: (workflowId: string, data: StartWorkflowPayload) =>
    api.post<Workflow>(`/workflows/${workflowId}/start`, data),
  pause: (workflowId: string) => api.post<Workflow>(`/workflows/${workflowId}/pause`),
}
