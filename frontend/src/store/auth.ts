import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  token: string | null
  userId: string | null
  username: string | null
  role: string | null
  setAuth: (data: {
    token: string
    userId: string
    username: string
    role: string
  }) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      userId: null,
      username: null,
      role: null,
      setAuth: (data) =>
        set({
          token: data.token,
          userId: data.userId,
          username: data.username,
          role: data.role,
        }),
      logout: () =>
        set({ token: null, userId: null, username: null, role: null }),
    }),
    { name: 'ai-collab-auth' }
  )
)
