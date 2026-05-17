import api from './client'

export interface ApiKeyResponse {
  id: string
  name: string
  key_prefix: string
  scopes: string
  is_active: boolean
  expires_at: string | null
  last_used_at: string | null
  created_at: string
}

export interface ApiKeyCreated extends ApiKeyResponse {
  raw_key: string
}

export interface ApiKeyCreateParams {
  name: string
  scopes?: string
  expires_at?: string | null
}

export const apiKeysApi = {
  list: () => api.get<ApiKeyResponse[]>('/api-keys'),

  create: (data: ApiKeyCreateParams) =>
    api.post<ApiKeyCreated>('/api-keys', data),

  revoke: (keyId: string) =>
    api.post<{ success: boolean; message: string }>(`/api-keys/${keyId}/revoke`),

  delete: (keyId: string) =>
    api.delete<{ success: boolean; message: string }>(`/api-keys/${keyId}`),
}
