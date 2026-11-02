const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

const ACCESS_KEY = "access_token"
const REFRESH_KEY = "refresh_token"
const USER_KEY = "auth_user"

/** Endpoints where a 401 means "bad input", not "your session expired". */
const NO_REFRESH_PATHS = ["/auth/login/", "/auth/register/", "/auth/refresh/", "/auth/verify-email/", "/auth/reset-password/", "/auth/forgot-password/"]

export class ApiError extends Error {
  constructor(message: string, public status: number, public code?: string) {
    super(message)
    this.name = "ApiError"
  }
}

function errorFromResponse(status: number, json: any): ApiError {
  if (json?.status === "error" && json.error) {
    const details = json.error.details
    const fields = details && typeof details === "object" && !Array.isArray(details)
      ? Object.entries(details).map(([field, msgs]) => `${field.replace(/_/g, " ")}: ${[msgs].flat().join(", ")}`)
      : []
    return new ApiError(fields.length ? fields.join("; ") : json.error.message || "Request failed", status, json.error.code)
  }
  if (json?.detail) return new ApiError(String(json.detail), status)
  if (json && typeof json === "object" && !Array.isArray(json)) {
    const flat = Object.values(json).flat().filter((v) => typeof v === "string").join("; ")
    if (flat) return new ApiError(flat, status)
  }
  return new ApiError("Request failed", status)
}

class ApiClient {
  private refreshing: Promise<boolean> | null = null

  getToken(): string | null {
    return typeof window === "undefined" ? null : localStorage.getItem(ACCESS_KEY)
  }

  getRefreshToken(): string | null {
    return typeof window === "undefined" ? null : localStorage.getItem(REFRESH_KEY)
  }

  setTokens(tokens: { access: string; refresh: string }) {
    localStorage.setItem(ACCESS_KEY, tokens.access)
    localStorage.setItem(REFRESH_KEY, tokens.refresh)
  }

  clearSession() {
    if (typeof window === "undefined") return
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
    localStorage.removeItem(USER_KEY)
  }

  /** Single-flight: refresh tokens rotate, so concurrent 401s must share one refresh call. */
  private refreshAccessToken(): Promise<boolean> {
    if (!this.refreshing) {
      this.refreshing = this.doRefresh().finally(() => { this.refreshing = null })
    }
    return this.refreshing
  }

  private async doRefresh(): Promise<boolean> {
    const refresh = this.getRefreshToken()
    if (!refresh) return false
    try {
      const res = await fetch(`${API_BASE}/auth/refresh/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh }),
      })
      if (res.ok) {
        const json = await res.json()
        const data = json?.status === "success" ? json.data : json
        localStorage.setItem(ACCESS_KEY, data.access)
        if (data.refresh) localStorage.setItem(REFRESH_KEY, data.refresh)
        return true
      }
    } catch {
      return false
    }
    // Another tab may have rotated the token first; its new one is then in storage.
    return this.getRefreshToken() !== refresh
  }

  private async request<T>(path: string, options: RequestInit = {}, isRetry = false): Promise<T> {
    const isForm = options.body instanceof FormData
    const headers: Record<string, string> = {
      ...(isForm ? {} : { "Content-Type": "application/json" }),
      ...(options.headers as Record<string, string>),
    }
    const token = this.getToken()
    if (token) headers["Authorization"] = `Bearer ${token}`

    const res = await fetch(`${API_BASE}${path}`, { ...options, headers })

    if (res.status === 401 && !NO_REFRESH_PATHS.some((p) => path.startsWith(p))) {
      if (!isRetry && (await this.refreshAccessToken())) {
        return this.request<T>(path, options, true)
      }
      this.clearSession()
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/auth/")) {
        window.location.href = "/auth/login"
      }
      throw new ApiError("Session expired. Please sign in again.", 401)
    }

    const json = await res.json().catch(() => null)

    if (!res.ok) throw errorFromResponse(res.status, json)
    if (res.status === 204) return undefined as T
    if (json?.status === "success") return json.data as T
    return json as T
  }

  get = <T>(path: string, params?: Record<string, unknown>) => {
    const entries = Object.entries(params ?? {}).filter(([, v]) => v !== undefined && v !== null && v !== "")
    const qs = entries.length ? "?" + new URLSearchParams(entries.map(([k, v]) => [k, String(v)])).toString() : ""
    return this.request<T>(`${path}${qs}`)
  }

  private encode(body: unknown): BodyInit | undefined {
    if (body === undefined || body === null) return undefined
    return body instanceof FormData ? body : JSON.stringify(body)
  }

  post = <T>(path: string, body?: unknown) =>
    this.request<T>(path, { method: "POST", body: this.encode(body) })

  patch = <T>(path: string, body?: unknown) =>
    this.request<T>(path, { method: "PATCH", body: this.encode(body) })

  put = <T>(path: string, body?: unknown) =>
    this.request<T>(path, { method: "PUT", body: this.encode(body) })

  delete = <T>(path: string) =>
    this.request<T>(path, { method: "DELETE" })
}

export const api = new ApiClient()

/** File fields come back relative (/media/...); they are served by the API host. */
export function mediaUrl(path?: string | null): string | null {
  if (!path) return null
  if (/^https?:\/\//.test(path)) return path
  return `${new URL(API_BASE).origin}${path}`
}
