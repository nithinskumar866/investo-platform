"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/services/api"
import type * as T from "@/types/api"

/**
 * Safely extracts an array from various Django REST Framework response shapes:
 * 1. Pure DRF pagination: { count, next, previous, results: [...] }
 * 2. Wrapped DRF pagination: { count, next, previous, results: { status: "success", data: [...] } }
 * 3. Already unwrapped or native array: [...]
 */
async function fetchArray<T>(path: string, params?: Record<string, unknown>): Promise<T[]> {
  try {
    const res = await api.get<any>(path, params)
    if (!res) return []
    if (res?.results?.data && Array.isArray(res.results.data)) return res.results.data
    if (res?.results !== undefined && Array.isArray(res.results)) return res.results
    if (res?.data && Array.isArray(res.data)) return res.data
    if (Array.isArray(res)) return res
    return []
  } catch (error) {
    throw error
  }
}

// ── Auth ─────────────────────────────────────────────────────────
export function useLogin() {
  return useMutation({
    mutationFn: (data: T.LoginRequest) =>
      api.post<T.AuthResponse>("/auth/login/", data),
  })
}

export function useRegister() {
  return useMutation({
    mutationFn: (data: T.RegisterRequest) =>
      api.post<T.AuthResponse>("/auth/register/", data),
  })
}

export function useVerifyOTP() {
  return useMutation({
    mutationFn: (data: T.VerifyOTPRequest) =>
      api.post<T.AuthResponse>("/auth/verify-email/", data),
  })
}

export function useResetPassword() {
  return useMutation({
    mutationFn: (data: { email: string; otp: string; password: string }) =>
      api.post<{ status: string; data: { message: string } }>("/auth/reset-password/", data),
  })
}


export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: () => api.get<T.User>("/auth/me/"),
    enabled: !!api.getToken(),
  })
}

export function useInvestors(params?: Record<string, unknown>) {
  return useQuery({
    queryKey: ["investors", params],
    queryFn: () => fetchArray<any>("/auth/profiles/investor/", params),
  })
}

// ── Notifications ────────────────────────────────────────────────
export function useNotifications(params?: { page?: number }) {
  return useQuery({
    queryKey: ["notifications", params],
    queryFn: () => fetchArray<T.Notification>("/notifications/", params as Record<string, unknown>),
  })
}

export function useUnreadCount() {
  return useQuery({
    queryKey: ["notifications", "unread"],
    queryFn: () => api.get<{ count: number }>("/notifications/unread-count/"),
    refetchInterval: 30000,
  })
}

export function useMarkRead() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.post(`/notifications/${id}/read/`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["notifications"] }) },
  })
}

// ── Startups ─────────────────────────────────────────────────────
export function useStartups(params?: T.StartupListParams) {
  return useQuery({
    queryKey: ["startups", params],
    queryFn: () => fetchArray<T.Startup>("/startups/", params as Record<string, unknown>),
  })
}

export function useStartup(slug: string) {
  return useQuery({
    queryKey: ["startup", slug],
    queryFn: () => api.get<T.Startup>(`/startups/${slug}/`),
    enabled: !!slug,
  })
}

export function useCreateStartup() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<T.Startup>) =>
      api.post<T.Startup>("/startups/", data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["startups"] })
      qc.invalidateQueries({ queryKey: ["analytics"] })
    },
  })
}

// ── Matches ──────────────────────────────────────────────────────
export function useMatches(type: "investor" | "startup") {
  const backendType = type === "startup" ? "investor" : "entrepreneur";
  return useQuery({
    queryKey: ["matches", type],
    queryFn: () => fetchArray<T.MatchScore>(`/matching/${backendType}/matches/`),
  })
}

export function useMatchInsight(matchId: number) {
  return useQuery({
    queryKey: ["match-insight", matchId],
    queryFn: () => api.get<T.MatchInsight>(`/matching/insights/${matchId}/`),
    enabled: !!matchId,
  })
}

// ── Chat ─────────────────────────────────────────────────────────
export function useConversations() {
  return useQuery({
    queryKey: ["conversations"],
    queryFn: () => fetchArray<T.Conversation>("/chat/conversations/"),
  })
}

export function useCreateConversation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { participant_id: number }) =>
      api.post<T.Conversation>("/chat/conversations/", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["conversations"] }),
  })
}

export function useMessages(conversationId: number) {
  return useQuery({
    queryKey: ["messages", conversationId],
    queryFn: () => fetchArray<T.Message>(`/chat/conversations/${conversationId}/messages/`),
    enabled: !!conversationId,
    refetchInterval: 5000,
  })
}

// ── Meetings ─────────────────────────────────────────────────────
export function useMeetings() {
  return useQuery({
    queryKey: ["meetings"],
    queryFn: () => fetchArray<T.Meeting>("/meetings/"),
  })
}

// ── Investments ──────────────────────────────────────────────────
export function useInvestments() {
  return useQuery({
    queryKey: ["investments"],
    queryFn: () => fetchArray<T.InvestmentOpportunity>("/investments/"),
  })
}

// ── Analytics ────────────────────────────────────────────────────
export function useFounderAnalytics(startupId?: number) {
  return useQuery({
    queryKey: ["analytics", "founder", startupId],
    queryFn: () => api.get<T.FounderDashboard>(
      startupId ? `/analytics/founder/dashboard/?startup_id=${startupId}` : `/analytics/founder/dashboard/`
    ),
  })
}

export function useFounderCharts(startupId?: number) {
  return useQuery({
    queryKey: ["analytics", "founder", "charts", startupId],
    queryFn: () => api.get<any>(
      startupId ? `/analytics/founder/charts/?startup_id=${startupId}` : `/analytics/founder/charts/`
    ),
  })
}

export function useFounderFunnel(startupId?: number) {
  return useQuery({
    queryKey: ["analytics", "founder", "funnel", startupId],
    queryFn: () => api.get<any>(
      startupId ? `/analytics/founder/funnel/?startup_id=${startupId}` : `/analytics/founder/funnel/`
    ),
  })
}

export function useInvestorAnalytics() {
  return useQuery({
    queryKey: ["analytics", "investor"],
    queryFn: () => api.get<T.InvestorDashboard>("/analytics/investor/dashboard/"),
  })
}

export function useInvestorCharts() {
  return useQuery({
    queryKey: ["analytics", "investor", "charts"],
    queryFn: () => api.get<any>("/analytics/investor/charts/"),
  })
}

// ── Activity Feed ────────────────────────────────────────────────
export function useFeed() {
  return useQuery({
    queryKey: ["feed"],
    queryFn: () => fetchArray<T.FeedActivity>("/activity/feed/"),
    refetchInterval: 15000,
  })
}

// ── Search ───────────────────────────────────────────────────────
export function useSearch(type: string, params: Record<string, unknown>) {
  return useQuery({
    queryKey: ["search", type, params],
    queryFn: () => api.get<T.SearchResult<unknown>>(`/search/${type}/`, params),
    enabled: false,
  })
}

// ── Billing ──────────────────────────────────────────────────────
export function usePlans() {
  return useQuery({
    queryKey: ["billing", "plans"],
    queryFn: () => fetchArray<T.SubscriptionPlan>("/billing/plans/"),
  })
}

export function useSubscription() {
  return useQuery({
    queryKey: ["billing", "subscription"],
    queryFn: () => api.get<T.UserSubscription | null>("/billing/subscription/"),
  })
}

export function useInvoices() {
  return useQuery({
    queryKey: ["billing", "invoices"],
    queryFn: () => fetchArray<T.Invoice>("/billing/invoices/"),
  })
}

export function useSubscribe() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { plan_slug: string; billing_cycle?: string; coupon_code?: string }) =>
      api.post<T.UserSubscription>("/billing/subscribe/", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["billing"] }),
  })
}

// ── Admin ────────────────────────────────────────────────────────
export function useAdminDashboard() {
  return useQuery({
    queryKey: ["admin", "dashboard"],
    queryFn: () => api.get<any>("/analytics/platform/overview/"),
  })
}

export function useAdminUsers(params?: Record<string, unknown>) {
  return useQuery({
    queryKey: ["admin", "users", params],
    queryFn: () => fetchArray<unknown>("/admin/users/", params),
  })
}

export function useAdminTickets() {
  return useQuery({
    queryKey: ["admin", "tickets"],
    queryFn: () => fetchArray<T.SupportTicket>("/admin/tickets/"),
  })
}

export function useAdminAuditLogs(params?: Record<string, unknown>) {
  return useQuery({
    queryKey: ["admin", "audit", params],
    queryFn: () => fetchArray<T.AuditLog>("/admin/audit/", params),
  })
}

export function useAdminRevenue() {
  return useQuery({
    queryKey: ["admin", "revenue"],
    queryFn: () => api.get<Record<string, unknown>>("/admin/revenue/"),
  })
}

// ── Observability ────────────────────────────────────────────────
export function useHealthCheck() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => api.get<Record<string, T.HealthCheck>>("/ops/health/"),
  })
}

export function useSystemMetrics() {
  return useQuery({
    queryKey: ["ops", "metrics"],
    queryFn: () => api.get<T.SystemMetrics>("/ops/metrics/"),
    refetchInterval: 30000,
  })
}
