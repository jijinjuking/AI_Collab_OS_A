import { create } from 'zustand'
import { projectApi, type Project, type ProjectListItem, type CreateProjectPayload } from '@/api/projects'

interface ProjectState {
  projects: ProjectListItem[]
  currentProject: Project | null
  loading: boolean
  error: string | null

  fetchProjects: () => Promise<void>
  fetchProject: (id: string) => Promise<void>
  createProject: (data: CreateProjectPayload) => Promise<Project>
  deleteProject: (id: string) => Promise<void>
  setCurrentProject: (project: Project | null) => void
}

export const useProjectStore = create<ProjectState>((set) => ({
  projects: [],
  currentProject: null,
  loading: false,
  error: null,

  fetchProjects: async () => {
    set({ loading: true, error: null })
    try {
      const res = await projectApi.list()
      set({ projects: res.data, loading: false })
    } catch (e: any) {
      set({ error: e.response?.data?.detail || '加载项目失败', loading: false })
    }
  },

  fetchProject: async (id: string) => {
    set({ loading: true, error: null })
    try {
      const res = await projectApi.get(id)
      set({ currentProject: res.data, loading: false })
    } catch (e: any) {
      set({ error: e.response?.data?.detail || '加载项目详情失败', loading: false })
    }
  },

  createProject: async (data: CreateProjectPayload) => {
    const res = await projectApi.create(data)
    set((state) => ({ projects: [{ ...res.data, description: res.data.description }, ...state.projects] }))
    return res.data
  },

  deleteProject: async (id: string) => {
    await projectApi.delete(id)
    set((state) => ({ projects: state.projects.filter((p) => p.id !== id) }))
  },

  setCurrentProject: (project) => set({ currentProject: project }),
}))
