import { create } from "zustand"
import { api } from "@/services/api"
import type { AuthTokens, User } from "@/types/api"

const USER_KEY = "auth_user"

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  /** False until the stored session has been read; guards wait for this before redirecting. */
  initialized: boolean
  setUser: (user: User | null) => void
  signIn: (user: User, tokens: AuthTokens) => void
  init: () => void
  logout: () => Promise<void>
}

function readCachedUser(): User | null {
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? (JSON.parse(raw) as User) : null
  } catch {
    return null
  }
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  initialized: false,
  setUser: (user) => {
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user))
    else localStorage.removeItem(USER_KEY)
    set({ user, isAuthenticated: !!user })
  },
  signIn: (user, tokens) => {
    api.setTokens(tokens)
    get().setUser(user)
    set({ initialized: true })
  },
  init: () => {
    if (get().initialized) return
    if (!api.getToken() && !api.getRefreshToken()) {
      set({ initialized: true })
      return
    }
    const cached = readCachedUser()
    if (cached) set({ user: cached, isAuthenticated: true, initialized: true })
    // Revalidate against the server. A dead session is handled inside the API client.
    api.get<User>("/auth/me/")
      .then((me) => get().setUser(me))
      .catch(() => {
        if (!api.getToken()) set({ user: null, isAuthenticated: false })
      })
      .finally(() => set({ initialized: true }))
  },
  logout: async () => {
    const refresh = api.getRefreshToken()
    try {
      if (refresh) await api.post("/auth/logout/", { refresh })
    } catch {
      // The local session is cleared regardless.
    }
    api.clearSession()
    set({ user: null, isAuthenticated: false })
    window.location.href = "/auth/login"
  },
}))
