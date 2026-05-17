import api from './client'

export interface Project {
  id: string
  user_id: string
  name: string
  description: string | null
  plan: string | null
  status: string
  config: Record<string, unknown> | null
  workspace_path: string | null
  created_at: string
  updated_at: string
}

export interface ProjectListItem {
  id: string
  name: string
  status: string
  description: string | null
  created_at: string
}

export interface CreateProjectPayload {
  name: string
  description?: string
  plan?: string
  config?: Record<string, unknown>
}

export interface UpdateProjectPayload {
  name?: string
  description?: string
  plan?: string
  status?: string
  config?: Record<string, unknown>
}

export const projectApi = {
  list: () => api.get<ProjectListItem[]>('/projects'),
  get: (id: string) => api.get<Project>(`/projects/${id}`),
  create: (data: CreateProjectPayload) => api.post<Project>('/projects', data),
  update: (id: string, data: UpdateProjectPayload) => api.patch<Project>(`/projects/${id}`, data),
  delete: (id: string) => api.delete(`/projects/${id}`),
}
