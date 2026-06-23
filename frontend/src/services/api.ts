const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

class ApiClient {
  private token: string | null = null

  setToken(token: string | null) {
    this.token = token
    if (typeof window !== "undefined") {
      if (token) localStorage.setItem("access_token", token)
      else localStorage.removeItem("access_token")
    }
  }

  getToken(): string | null {
    if (this.token) return this.token
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("access_token")
    }
    return this.token
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    }
    const token = this.getToken()
    if (token) headers["Authorization"] = `Bearer ${token}`

    const res = await fetch(`${API_BASE}${path}`, { ...options, headers })

    if (res.status === 401) {
      this.setToken(null)
      if (typeof window !== "undefined") window.location.href = "/auth/login"
      throw new Error("Session expired. Please sign in again.")
    }

    const json = await res.json().catch(() => null)

    if (!res.ok) {
      if (json?.status === "error") {
        throw new Error(json.error?.message || "Request failed")
      }
      if (json && typeof json === "object" && !Array.isArray(json)) {
        const fieldErrors = Object.values(json).flat().filter(Boolean).join("; ")
        if (fieldErrors) throw new Error(fieldErrors)
      }
      throw new Error(json?.detail || json?.message || "Request failed")
    }

    if (res.status === 204) return undefined as T

    if (json?.status === "success") return json.data as T
    return json as T
  }

  get = <T>(path: string, params?: Record<string, unknown>) => {
    const qs = params ? "?" + new URLSearchParams(
      Object.entries(params).filter(([_, v]) => v !== undefined).map(([k, v]) => [k, String(v)])
    ).toString() : ""
    return this.request<T>(`${path}${qs}`)
  }

  post = <T>(path: string, body?: unknown) =>
    this.request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined })

  patch = <T>(path: string, body?: unknown) =>
    this.request<T>(path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined })

  put = <T>(path: string, body?: unknown) =>
    this.request<T>(path, { method: "PUT", body: body ? JSON.stringify(body) : undefined })

  delete = <T>(path: string) =>
    this.request<T>(path, { method: "DELETE" })
}

export const api = new ApiClient()
