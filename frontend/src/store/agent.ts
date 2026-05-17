import { create } from 'zustand'
import { agentApi, type AgentInstance, type RoleTemplate, type CreateAgentPayload, type UpdateAgentPayload } from '@/api/agents'

interface AgentState {
  roles: RoleTemplate[]
  agents: AgentInstance[]
  loading: boolean
  error: string | null

  fetchRoles: () => Promise<void>
  fetchAgents: (projectId: string) => Promise<void>
  createAgent: (projectId: string, data: CreateAgentPayload) => Promise<AgentInstance>
  updateAgent: (agentId: string, data: UpdateAgentPayload) => Promise<void>
  deleteAgent: (agentId: string) => Promise<void>
}

export const useAgentStore = create<AgentState>((set) => ({
  roles: [],
  agents: [],
  loading: false,
  error: null,

  fetchRoles: async () => {
    try {
      const res = await agentApi.listRoles()
      set({ roles: res.data })
    } catch (e: any) {
      set({ error: e.response?.data?.detail || '加载角色失败' })
    }
  },

  fetchAgents: async (projectId: string) => {
    set({ loading: true, error: null })
    try {
      const res = await agentApi.listAgents(projectId)
      set({ agents: res.data, loading: false })
    } catch (e: any) {
      set({ error: e.response?.data?.detail || '加载 Agent 失败', loading: false })
    }
  },

  createAgent: async (projectId: string, data: CreateAgentPayload) => {
    const res = await agentApi.createAgent(projectId, data)
    set((state) => ({ agents: [...state.agents, res.data] }))
    return res.data
  },

  updateAgent: async (agentId: string, data: UpdateAgentPayload) => {
    const res = await agentApi.updateAgent(agentId, data)
    set((state) => ({
      agents: state.agents.map((a) => (a.id === agentId ? res.data : a)),
    }))
  },

  deleteAgent: async (agentId: string) => {
    await agentApi.deleteAgent(agentId)
    set((state) => ({ agents: state.agents.filter((a) => a.id !== agentId) }))
  },
}))
