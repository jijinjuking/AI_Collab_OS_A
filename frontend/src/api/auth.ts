import api from './client'

export interface LoginPayload {
  username: string
  password: string
}

export interface RegisterPayload {
  username: string
  password: string
  email?: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user_id: string
  username: string
  role: string
}

export interface UserInfo {
  id: string
  username: string
  email: string | null
  role: string
  settings: Record<string, unknown> | null
}

export const authApi = {
  login: (data: LoginPayload) =>
    api.post<TokenResponse>('/auth/login', data),

  register: (data: RegisterPayload) =>
    api.post<TokenResponse>('/auth/register', data),

  getMe: () => api.get<UserInfo>('/auth/me'),
}
