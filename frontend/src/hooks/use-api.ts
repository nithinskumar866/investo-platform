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
async function fetchArray<R>(path: string, params?: Record<string, unknown>): Promise<R[]> {
  const res = await api.get<any>(path, params)
  if (!res) return []
  if (res?.results?.data && Array.isArray(res.results.data)) return res.results.data
  if (res?.results !== undefined && Array.isArray(res.results)) return res.results
  if (res?.data && Array.isArray(res.data)) return res.data
  if (Array.isArray(res)) return res
  return []
}

// ── Auth ─────────────────────────────────────────────────────────
export function useLogin() {
  return useMutation({
    mutationFn: (data: T.LoginRequest) => api.post<T.AuthResponse>("/auth/login/", data),
    meta: { silent: true },
  })
}

export function useRegister() {
  return useMutation({
    mutationFn: (data: T.RegisterRequest) => api.post<T.AuthResponse>("/auth/register/", data),
  })
}

export function useVerifyOTP() {
  return useMutation({
    mutationFn: (data: T.VerifyOTPRequest) => api.post<T.AuthResponse>("/auth/verify-email/", data),
  })
}

export function useResendVerification() {
  return useMutation({
    mutationFn: (email: string) => api.post("/auth/resend-verification/", { email }),
  })
}

export function useForgotPassword() {
  return useMutation({
    mutationFn: (email: string) => api.post("/auth/forgot-password/", { email }),
  })
}

export function useResetPassword() {
  return useMutation({
    mutationFn: (data: { email: string; otp: string; password: string; confirm_password: string }) =>
      api.post("/auth/reset-password/", data),
  })
}

export function useInvestors(params?: Record<string, unknown>) {
  return useQuery({
    queryKey: ["investors", params],
    queryFn: () => fetchArray<any>("/auth/profiles/investor/", params),
  })
}

// ── Notifications ────────────────────────────────────────────────
export function useNotifications() {
  return useQuery({
    queryKey: ["notifications", "list"],
    queryFn: () => fetchArray<T.Notification>("/notifications/"),
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

export function useMarkAllRead() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.post("/notifications/read-all/"),
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

export function useMyStartups(enabled = true) {
  return useQuery({
    queryKey: ["startups", "mine"],
    queryFn: () => fetchArray<T.Startup>("/startups/my_startups/", { per_page: 100 }),
    enabled,
  })
}

export function useStartup(id: number) {
  return useQuery({
    queryKey: ["startup", id],
    queryFn: () => api.get<T.StartupDetail>(`/startups/${id}/`),
    enabled: !!id,
    meta: { silent: true },
  })
}

export function useFundingProgress(id: number) {
  return useQuery({
    queryKey: ["startup", id, "funding"],
    queryFn: () => api.get<T.FundingProgress>(`/startups/${id}/funding_progress/`),
    enabled: !!id,
  })
}

function invalidateStartups(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: ["startups"] })
  qc.invalidateQueries({ queryKey: ["startup"] })
  qc.invalidateQueries({ queryKey: ["analytics"] })
}

export function useCreateStartup() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => api.post<T.StartupDetail>("/startups/", data),
    onSuccess: () => invalidateStartups(qc),
  })
}

export function useUpdateStartup(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => api.patch<T.StartupDetail>(`/startups/${id}/`, data),
    onSuccess: () => invalidateStartups(qc),
  })
}

export function useDeleteStartup() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.delete(`/startups/${id}/`),
    onSuccess: () => invalidateStartups(qc),
  })
}

export function usePublishStartup() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.post(`/startups/${id}/publish/`),
    onSuccess: () => {
      invalidateStartups(qc)
      qc.invalidateQueries({ queryKey: ["matches"] })
    },
  })
}

export function useStartupDocuments(id: number) {
  return useQuery({
    queryKey: ["startup", id, "documents"],
    queryFn: () => api.get<T.StartupDocument[]>(`/startups/${id}/documents/`),
    enabled: !!id,
  })
}

export function useUploadStartupDocument(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (form: FormData) => api.post(`/startups/${id}/upload_document/`, form),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["startup", id, "documents"] }),
  })
}

export function useDeleteStartupDocument(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (docId: number) => api.delete(`/startups/${id}/documents/${docId}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["startup", id, "documents"] }),
  })
}

// ── Matches ──────────────────────────────────────────────────────
export function useMatches(type: "investor" | "startup", enabled = true) {
  const backendType = type === "startup" ? "investor" : "entrepreneur"
  return useQuery({
    queryKey: ["matches", type],
    queryFn: async () => {
      const rows = await fetchArray<T.MatchScore>(`/matching/${backendType}/matches/`, { per_page: 100 })
      return rows.map((m) => ({ ...m, score: Number(m.score) }))
    },
    enabled,
  })
}

export function useSaveMatch() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.post(`/matching/investor/matches/${id}/save/`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["matches"] })
      qc.invalidateQueries({ queryKey: ["analytics"] })
    },
  })
}

export function useSavedMatches() {
  return useQuery({
    queryKey: ["matches", "saved"],
    queryFn: async () => {
      const rows = await fetchArray<T.SavedMatch>("/matching/investor/matches/saved/")
      return rows.map((r) => ({ ...r.match_details, score: Number(r.match_details.score) }))
    },
  })
}

export function useMatchInsight(matchId: number | undefined) {
  return useQuery({
    queryKey: ["match-insight", matchId],
    queryFn: () => api.get<T.MatchInsight>(`/matching/insights/${matchId}/`),
    enabled: !!matchId,
    retry: false,
    staleTime: 5 * 60 * 1000,
    meta: { silent: true },
  })
}

export function useRegenerateInsight(matchId: number | undefined) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.post<T.MatchInsight>(`/matching/insights/${matchId}/regenerate/`),
    onSuccess: (data) => qc.setQueryData(["match-insight", matchId], data),
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
    mutationFn: (data: { participant_id: number }) => api.post<T.Conversation>("/chat/conversations/", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["conversations"] }),
  })
}

export function useMessages(conversationId: number) {
  return useQuery({
    queryKey: ["messages", conversationId],
    // The API returns newest first; the thread reads oldest first.
    queryFn: async () => (await fetchArray<T.Message>(`/chat/conversations/${conversationId}/messages/`)).reverse(),
    enabled: !!conversationId,
    refetchInterval: 5000,
  })
}

export function useSendMessage(conversationId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (content: string) => api.post<T.Message>(`/chat/conversations/${conversationId}/messages/`, { content }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["messages", conversationId] })
      qc.invalidateQueries({ queryKey: ["conversations"] })
    },
  })
}

// ── Meetings ─────────────────────────────────────────────────────
export function useMeetings() {
  return useQuery({
    queryKey: ["meetings"],
    queryFn: () => fetchArray<T.Meeting>("/meetings/", { limit: 100 }),
  })
}

export function useCreateMeeting() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: T.CreateMeetingRequest) => api.post<T.Meeting>("/meetings/", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["meetings"] }),
  })
}

export function useMeetingAction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, action }: { id: number; action: "confirm" | "cancel" | "complete" }) =>
      api.post(`/meetings/${id}/${action}/`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["meetings"] }),
  })
}

// ── Deals ────────────────────────────────────────────────────────
export function useInvestorDeals(enabled = true) {
  return useQuery({
    queryKey: ["deals", "investor"],
    queryFn: () => fetchArray<T.Deal>("/investments/pipeline/investor/", { per_page: 100 }),
    enabled,
  })
}

/** The startup-side pipeline is per startup, so a founder's board combines all of theirs. */
export function useFounderDeals(startupIds: number[] | undefined) {
  return useQuery({
    queryKey: ["deals", "founder", startupIds],
    queryFn: async () => {
      const lists = await Promise.all((startupIds ?? []).map((id) =>
        fetchArray<T.Deal>("/investments/pipeline/startup/", { startup_id: id, per_page: 100 }),
      ))
      return lists.flat()
    },
    enabled: !!startupIds,
  })
}

/** Only the detail response carries founder_accepted_at and the term sheet link. */
export function useDealDetail(id: number, side: "investor" | "startup", enabled = true) {
  return useQuery({
    queryKey: ["deals", "detail", side, id],
    queryFn: () => api.get<T.DealDetail>(`/investments/pipeline/${side}/${id}/`),
    enabled,
  })
}

function useDealMutation<V>(fn: (vars: V) => Promise<unknown>) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["deals"] })
      qc.invalidateQueries({ queryKey: ["startup"] })
      qc.invalidateQueries({ queryKey: ["startups"] })
      qc.invalidateQueries({ queryKey: ["analytics"] })
    },
  })
}

export function useExpressInterest() {
  return useDealMutation((data: { startup_id: number; amount_requested?: string; notes?: string }) =>
    api.post<T.DealDetail>("/investments/pipeline/investor/", data))
}

export function useDealAction(side: "investor" | "startup") {
  return useDealMutation(({ id, action, body }: { id: number; action: string; body?: Record<string, unknown> }) =>
    api.post<T.DealDetail>(`/investments/pipeline/${side}/${id}/${action}/`, body ?? {}))
}

// ── Data Room ────────────────────────────────────────────────────
export function useDataRooms(startupId: number | undefined) {
  return useQuery({
    queryKey: ["data-room", "rooms", startupId],
    queryFn: () => api.get<T.DataRoom[]>("/data-room/rooms/", { startup_id: startupId }),
    enabled: !!startupId,
  })
}

export function useDataRoom(id: number | null) {
  return useQuery({
    queryKey: ["data-room", "room", id],
    queryFn: () => api.get<T.DataRoomDetail>(`/data-room/rooms/${id}/`),
    enabled: !!id,
  })
}

export function useCreateDataRoom() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { startup_id: number; title: string; description?: string; visibility?: string }) =>
      api.post<T.DataRoomDetail>("/data-room/rooms/", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["data-room"] }),
  })
}

export function useDeleteDataRoom() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.delete(`/data-room/rooms/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["data-room"] }),
  })
}

export function useUploadRoomDocument(roomId: number | null) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (form: FormData) => api.post(`/data-room/rooms/${roomId}/upload/`, form),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["data-room"] }),
  })
}

export function useDeleteRoomDocument() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.delete(`/data-room/documents/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["data-room"] }),
  })
}

export function useAccessRequests() {
  return useQuery({
    queryKey: ["data-room", "access-requests"],
    queryFn: () => api.get<T.AccessRequest[]>("/data-room/access-requests/"),
  })
}

export function useDecideAccessRequest() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, decision }: { id: number; decision: "approve" | "deny" }) =>
      api.post(`/data-room/access-requests/${id}/${decision}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["data-room"] }),
  })
}

export function useInvestorRooms(startupId?: number) {
  return useQuery({
    queryKey: ["data-room", "investor", "rooms", startupId],
    queryFn: () => api.get<T.InvestorRoom[]>("/data-room/investor/rooms/", { startup_id: startupId }),
  })
}

export function useInvestorDocuments() {
  return useQuery({
    queryKey: ["data-room", "investor", "documents"],
    queryFn: () => api.get<T.DataRoomDocument[]>("/data-room/investor/documents/"),
  })
}

export function useRequestRoomAccess() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, message }: { id: number; message?: string }) =>
      api.post(`/data-room/investor/rooms/${id}/request_access/`, { message: message ?? "" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["data-room"] }),
  })
}

// ── Analytics ────────────────────────────────────────────────────
export function useFounderAnalytics(startupId?: number) {
  return useQuery({
    queryKey: ["analytics", "founder", startupId],
    queryFn: () => api.get<T.FounderDashboard>("/analytics/founder/dashboard/", { startup_id: startupId }),
  })
}

export function useFounderCharts(startupId?: number) {
  return useQuery({
    queryKey: ["analytics", "founder", "charts", startupId],
    queryFn: () => api.get<any>("/analytics/founder/charts/", { startup_id: startupId }),
  })
}

export function useFounderFunnel(startupId?: number) {
  return useQuery({
    queryKey: ["analytics", "founder", "funnel", startupId],
    queryFn: () => api.get<any>("/analytics/founder/funnel/", { startup_id: startupId }),
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

export function useTrendingFeed() {
  return useQuery({
    queryKey: ["feed", "trending"],
    queryFn: () => fetchArray<T.FeedActivity>("/activity/feed/trending/", { limit: 5 }),
  })
}

// ── Search ───────────────────────────────────────────────────────
export function useSearch(type: string, params: Record<string, unknown>, enabled: boolean) {
  return useQuery({
    queryKey: ["search", type, params],
    queryFn: () => api.get<{ results: Record<string, any>[] }>(`/search/${type}/`, params),
    enabled,
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

export function useBillingAction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (action: "cancel" | "renew") => api.post<T.UserSubscription>(`/billing/${action}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["billing"] }),
  })
}

// ── Admin ────────────────────────────────────────────────────────
export function useAdminDashboard() {
  return useQuery({
    queryKey: ["admin", "dashboard"],
    queryFn: () => api.get<T.AdminDashboard>("/admin/dashboard/"),
  })
}

export function useAdminUsers(params?: Record<string, unknown>) {
  return useQuery({
    queryKey: ["admin", "users", params],
    queryFn: () => fetchArray<T.AdminUser>("/admin/users/", params),
  })
}

export function useAdminUserAction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, action, body }: { id: number; action: "suspend" | "restore" | "verify"; body?: Record<string, unknown> }) =>
      api.post(`/admin/users/${id}/${action}/`, body ?? {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin"] }),
  })
}

export function useAdminStartups(params?: Record<string, unknown>) {
  return useQuery({
    queryKey: ["admin", "startups", params],
    queryFn: () => fetchArray<T.AdminStartup>("/admin/startups/", params),
  })
}

export function useAdminStartupAction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, action }: { id: number; action: "approve" | "reject" | "archive" | "flag" | "verify" }) =>
      action === "verify"
        ? api.post(`/admin/startups/${id}/verify/`, { verified: true })
        : api.post(`/admin/startups/${id}/moderate/`, { action }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin"] })
      qc.invalidateQueries({ queryKey: ["startups"] })
    },
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
    queryFn: () => api.get<T.AdminRevenue>("/admin/revenue/"),
  })
}

export function useAdminRisk() {
  return useQuery({
    queryKey: ["admin", "risk"],
    queryFn: () => api.get<T.AdminRisk>("/admin/risk/"),
  })
}

// ── Observability ────────────────────────────────────────────────
export function useHealthCheck() {
  return useQuery({
    queryKey: ["ops", "health"],
    queryFn: () => api.get<T.OpsHealth>("/ops/health/"),
  })
}

export function useSystemMetrics() {
  return useQuery({
    queryKey: ["ops", "metrics"],
    queryFn: () => api.get<T.SystemMetrics>("/ops/metrics/"),
    refetchInterval: 30000,
  })
}

export function useOpsAlerts() {
  return useQuery({
    queryKey: ["ops", "alerts"],
    queryFn: () => api.get<T.OpsAlerts>("/ops/alerts/"),
  })
}

export function useOpsErrors(severity?: string) {
  return useQuery({
    queryKey: ["ops", "errors", severity],
    queryFn: () => api.get<T.OpsErrors>("/ops/errors/", { severity }),
  })
}
