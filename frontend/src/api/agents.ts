import api from './client'

export interface RoleTemplate {
  id: string
  key: string
  name: string
  icon: string | null
  system_prompt: string
  skills: string[] | null
  default_model: string | null
  is_system: boolean
  user_id: string | null
}

export interface AgentInstance {
  id: string
  project_id: string
  role_template_id: string
  instance_name: string
  instance_index: number
  status: string
  provider: string | null
  base_url: string | null
  model: string | null
  system_prompt_override: string | null
  config: Record<string, unknown> | null
  token_used: number
  created_at: string
  updated_at: string
}

export interface CreateAgentPayload {
  role_template_id: string
  instance_name: string
  provider?: string
  base_url?: string
  model?: string
  system_prompt_override?: string
  config?: Record<string, unknown>
}

export interface UpdateAgentPayload {
  instance_name?: string
  provider?: string
  base_url?: string
  model?: string
  system_prompt_override?: string
  config?: Record<string, unknown>
  status?: string
}

export const agentApi = {
  // Role templates
  listRoles: () => api.get<RoleTemplate[]>('/roles'),
  getRole: (id: string) => api.get<RoleTemplate>(`/roles/${id}`),

  // Agent instances
  listAgents: (projectId: string) => api.get<AgentInstance[]>(`/agents/project/${projectId}`),
  createAgent: (projectId: string, data: CreateAgentPayload) =>
    api.post<AgentInstance>(`/agents/project/${projectId}`, data),
  updateAgent: (agentId: string, data: UpdateAgentPayload) =>
    api.patch<AgentInstance>(`/agents/${agentId}`, data),
  deleteAgent: (agentId: string) => api.delete(`/agents/${agentId}`),
}
