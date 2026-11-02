// Numeric money fields arrive from DRF as strings ("500000.00").
export type Decimal = string | number

// ── Auth ─────────────────────────────────────────────────────────
export interface LoginRequest { email: string; password: string }
export interface RegisterRequest { email: string; password: string; confirm_password: string; first_name: string; last_name: string; role: "entrepreneur" | "investor" }
export interface VerifyOTPRequest { email: string; otp: string }
export interface AuthTokens { access: string; refresh: string }
export interface AuthResponse { user: User; tokens: AuthTokens }
export interface User { id: number; email: string; first_name: string; last_name: string; role: string; avatar: string | null; is_verified: boolean; phone: string; date_joined?: string }

// ── Startups ─────────────────────────────────────────────────────
export interface Startup { id: number; name: string; slug: string; tagline: string; industry: string; stage: string; status: string; funding_goal: Decimal | null; equity_offered: Decimal | null; location: string; logo: string | null; team_size: number | null; is_verified: boolean; view_count: number; bookmark_count: number; owner_name: string; created_at: string }
export interface TeamMember { id?: number; name: string; role: string; email?: string; bio?: string; is_founder?: boolean }
export interface StartupMetrics { monthly_revenue: Decimal | null; annual_revenue: Decimal | null; revenue_growth_pct: Decimal | null; monthly_active_users: number | null; total_users: number | null; gross_margin_pct: Decimal | null; burn_rate: Decimal | null; runway_months: number | null; traction_description: string; key_achievements: unknown }
export interface FundingRound { id: number; round_name: string; amount: Decimal | null; date: string | null; investors: unknown; valuation: Decimal | null; notes: string }
export interface StartupDocument { id: number; name: string; file: string; document_type: string; uploaded_at: string }
export interface StartupDetail extends Startup { short_description: string; description: string; detailed_pitch: string; business_model: string; min_funding: Decimal | null; max_funding: Decimal | null; valuation: Decimal | null; currency: string; website: string; founded_date: string | null; is_visible: boolean; updated_at: string; team_members?: TeamMember[]; funding_rounds?: FundingRound[]; metrics?: StartupMetrics | null; documents?: StartupDocument[] }
export interface StartupListParams { page?: number; industry?: string; stage?: string; status?: string; search?: string; ordering?: string; per_page?: number }
export interface FundingProgress { goal: Decimal | null; raised: Decimal; committed: Decimal; currency: string; investor_count: number; percent_raised: number }

// ── Matching ─────────────────────────────────────────────────────
export interface MatchScore { id: number; investor_id: number; startup_id: number; score: number; score_breakdown: Record<string, number>; status: string; is_viewed: boolean; is_bookmarked: boolean; created_at: string; startup_name: string; startup_slug: string; startup_logo: string | null; startup_industry: string; startup_stage: string; startup_location: string; startup_tagline: string; startup_funding_goal: Decimal | null; startup_owner_name: string; startup_owner_id: number; investor_name: string; investor_type: string | null }
export interface SavedMatch { id: number; match: number; match_details: MatchScore; created_at: string }
export interface InsightStrength { factor: string; label: string; score: number; weight: number; contribution: number; description: string }
export interface InsightRisk { factor: string; label: string; score: number; weight: number; impact: number; description: string }
export interface InsightRecommendation { target: string; action: string; detail: string; priority: string }
export interface MatchInsight { id: number; match_id: number; summary: string; strengths: InsightStrength[]; risks: InsightRisk[]; recommendations: InsightRecommendation[]; generated_at: string }

// ── Chat ─────────────────────────────────────────────────────────
export interface ChatParticipant { id: number; email?: string; first_name: string; last_name: string; avatar: string | null; role?: string }
export interface ChatMessageSummary { id: number; sender_id: number; message_type: string; content: string; created_at: string }
export interface Conversation { id: number; created_at: string; updated_at: string; participants?: ChatParticipant[]; other_participant?: ChatParticipant; latest_message?: ChatMessageSummary | null; unread?: number }
export interface Message { id: number; sender?: ChatParticipant; sender_id?: number; content: string; message_type: string; attachment?: string | null; edited_at?: string | null; created_at: string; read_by: { user_id: number; read_at: string }[] }

// ── Investments ──────────────────────────────────────────────────
export interface DealStartup { id: number; name: string; slug: string; industry: string; stage: string; logo: string | null; location: string; tagline?: string; funding_goal?: Decimal | null }
export interface DealInvestor { id: number; first_name: string; last_name: string; email: string; investor_type: string | null }
export interface Deal { id: number; startup: DealStartup; investor: DealInvestor; amount_requested: Decimal | null; amount_offered: Decimal | null; equity_requested: Decimal | null; equity_offered: Decimal | null; valuation: Decimal | null; proposed_valuation: Decimal | null; status: string; created_at: string; updated_at: string }
export interface DealActivity { id: number; actor: { id: number; first_name: string; last_name: string; email: string } | null; action: string; metadata: Record<string, unknown>; timestamp: string }
export interface DealDetail extends Deal { notes: string; term_sheet_url: string; founder_accepted_at: string | null; activities: DealActivity[] }

// ── Meetings ─────────────────────────────────────────────────────
export interface Meeting { id: number; title: string; meeting_type: string; status: string; scheduled_start: string; scheduled_end: string; timezone: string; meeting_link: string; location: string; organizer: number; organizer_email: string; investor: number; investor_email: string; startup: number | null; startup_name: string | null; participant_count: number; created_at: string }
export interface CreateMeetingRequest { title: string; description?: string; meeting_type: string; investor_id?: number; startup?: number | null; scheduled_start: string; scheduled_end: string; timezone?: string }

// ── Notifications ────────────────────────────────────────────────
export interface Notification { id: number; notification_type: string; category: string; title: string; message: string; is_read: boolean; data: Record<string, unknown>; relative_time?: string; created_at: string }

// ── Data Room ────────────────────────────────────────────────────
export interface DataRoom { id: number; title: string; description: string; visibility: string; document_count: number; created_at: string; updated_at: string }
export interface DataRoomDocument { id: number; data_room: number; title: string; document_type: string; version: number; file_size: number; mime_type: string; uploaded_by_email?: string; signed_url: string | null; created_at: string }
export interface DataRoomDetail extends Omit<DataRoom, "document_count"> { startup: number; documents: DataRoomDocument[] }
export type RoomAccessStatus = "none" | "pending" | "approved" | "denied"
export interface InvestorRoom { id: number; title: string; description: string; startup_id: number; startup_name: string; access_status: RoomAccessStatus }
export interface AccessRequest { id: number; data_room_id: number; data_room_title: string; startup_name: string; investor_id: number; investor_name: string; status: "pending" | "approved" | "denied"; message: string; created_at: string; decided_at: string | null }

// ── Activity Feed ────────────────────────────────────────────────
export interface FeedActivity { id: number; activity_type: string; title: string; description: string; actor_data?: { id: number; email: string; role: string; name: string }; startup: number | null; startup_name: string | null; investor: number | null; reaction_count?: number; comment_count?: number; created_at: string }

// ── Billing ──────────────────────────────────────────────────────
export interface SubscriptionPlan { id: number; name: string; slug: string; tier: string; description: string; monthly_price: Decimal; yearly_price: Decimal; features: Record<string, boolean | number | string>; limits: Record<string, number>; is_popular: boolean }
export interface UserSubscription { id: number; plan: SubscriptionPlan; status: string; billing_cycle: string; start_date: string | null; end_date: string | null; auto_renew: boolean }
export interface Invoice { id: number; invoice_number: string; amount: Decimal; currency: string; status: string; billing_cycle: string; plan_name: string; period_start: string | null; period_end: string | null; paid_at: string | null; created_at: string }

// ── Analytics ────────────────────────────────────────────────────
export interface KpiCard { value: number; growth?: number; [key: string]: unknown }
export interface FounderDashboard { kpi_cards: Record<string, KpiCard>; funding_progress: { goal?: number; raised: number; percentage: number } }
export interface InvestorDashboard { kpi_cards: Record<string, KpiCard>; deal_pipeline: { total: number; by_status: Record<string, number>; total_amount_requested: number; total_amount_offered: number }; meeting_stats: Record<string, number>; response_rate: { response_rate: number }; sector_distribution: { startup__industry: string; count: number; avg_score: number }[] }

// ── Admin ────────────────────────────────────────────────────────
export interface AdminDashboard { total_users: number; total_founders: number; total_investors: number; active_subscriptions: number; total_startups: number; active_deals: number; closed_deals: number; new_matches_30d: number; open_tickets: number }
export interface AdminUser { id: number; email: string; first_name: string; last_name: string; role: string; is_active: boolean; is_verified: boolean; date_joined: string | null }
export interface AdminStartup { id: number; name: string; industry: string; stage: string; status: string; is_verified: boolean; is_visible: boolean; owner_email: string; created_at: string }
export interface AdminRisk { excessive_messaging: { sender__email: string; sender_id: number; msg_count: number }[]; rapid_activity: { actor__email: string; actor_id: number; activity_count: number }[]; recent_bans_24h: number }
export interface AdminRevenue { mrr: number; arr: number; last_month_revenue: number; total_revenue: number; active_subscriptions: number; plan_distribution: { plan__tier: string; plan__name: string; count: number }[]; churned_this_month: number; trial_active: number; trial_converted: number }
export interface AuditLog { id: number; actor_email: string | null; action_type: string; target_type: string; target_repr: string; description: string; created_at: string }
export interface SupportTicket { id: number; user: number; user_email: string; subject: string; category: string; priority: string; status: string; assigned_to: number | null; created_at: string; updated_at: string }

// ── Observability ────────────────────────────────────────────────
export interface HealthCheck { status: string; detail: string }
export interface OpsHealth { overall: string; services: Record<string, HealthCheck> }
export interface SystemMetrics { api: { total_requests: number; avg_duration_ms: number; max_duration_ms: number; error_rate: number; top_endpoints: { endpoint: string; count: number; avg_duration: number }[] }; realtime: Record<string, number>; system: Record<string, number>; queue: Record<string, number> }
export interface OpsAlerts { summary: { total: number; triggered: number; resolved: number }; alerts: { id: number; rule_name: string; metric: string; metric_value: number; threshold: number; status: string; created_at: string }[] }
export interface OpsErrors { summary: { total: number }; errors: { id: number; source: string; severity: string; error_type: string; message: string; user_email: string | null; created_at: string }[] }
