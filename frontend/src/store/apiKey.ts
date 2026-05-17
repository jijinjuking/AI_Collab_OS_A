import { create } from 'zustand'
import { apiKeysApi, ApiKeyResponse, ApiKeyCreated } from '@/api/apiKeys'
import { toast } from '@/store/toast'

interface ApiKeyState {
  keys: ApiKeyResponse[]
  loading: boolean
  newlyCreated: ApiKeyCreated | null
  fetchKeys: () => Promise<void>
  createKey: (name: string, scopes?: string, expiresAt?: string | null) => Promise<void>
  revokeKey: (keyId: string) => Promise<void>
  deleteKey: (keyId: string) => Promise<void>
  clearNewlyCreated: () => void
}

export const useApiKeyStore = create<ApiKeyState>((set) => ({
  keys: [],
  loading: false,
  newlyCreated: null,

  fetchKeys: async () => {
    set({ loading: true })
    try {
      const res = await apiKeysApi.list()
      set({ keys: res.data })
    } catch {
      // Error handled by global interceptor
    } finally {
      set({ loading: false })
    }
  },

  createKey: async (name, scopes, expiresAt) => {
    try {
      const res = await apiKeysApi.create({
        name,
        scopes: scopes || 'read,write',
        expires_at: expiresAt || null,
      })
      set({ newlyCreated: res.data })
      toast.success('API Key 创建成功，请立即复制保存')
      // Refresh list
      const listRes = await apiKeysApi.list()
      set({ keys: listRes.data })
    } catch {
      // Error handled by global interceptor
    }
  },

  revokeKey: async (keyId) => {
    try {
      await apiKeysApi.revoke(keyId)
      toast.success('API Key 已撤销')
      const res = await apiKeysApi.list()
      set({ keys: res.data })
    } catch {
      // Error handled by global interceptor
    }
  },

  deleteKey: async (keyId) => {
    try {
      await apiKeysApi.delete(keyId)
      toast.success('API Key 已删除')
      const res = await apiKeysApi.list()
      set({ keys: res.data })
    } catch {
      // Error handled by global interceptor
    }
  },

  clearNewlyCreated: () => set({ newlyCreated: null }),
}))
