// ── Auth ─────────────────────────────────────────────────────────
export interface LoginRequest { email: string; password: string }
export interface RegisterRequest { email: string; password: string; confirm_password: string; first_name: string; last_name: string; role: "entrepreneur" | "investor" }
export interface VerifyOTPRequest { email: string; otp: string }
export interface AuthTokens { access: string; refresh: string }
export interface AuthResponse { user: User; tokens: AuthTokens }
export interface User { id: number; email: string; first_name: string; last_name: string; role: string; avatar: string | null; is_verified: boolean; is_active: boolean; phone: string }

// ── Startups ─────────────────────────────────────────────────────
export interface Startup { id: number; name: string; slug: string; tagline: string; description: string; industry: string; stage: string; status: string; funding_goal: number | null; valuation: number | null; location: string; team_size: number | null; founded_date: string | null; is_verified: boolean; is_visible: boolean; view_count: number; owner: number; created_at: string }
export interface StartupListParams { page?: number; industry?: string; stage?: string; status?: string; search?: string; ordering?: string }

// ── Matching ─────────────────────────────────────────────────────
export interface MatchScore { id: number; investor: number; startup: number; score: number; status: string; is_viewed: boolean; is_bookmarked: boolean; created_at: string; startup_detail?: Startup; investor_detail?: User }
export interface MatchInsight { id: number; match_score: number; summary: string; strengths: string[]; risks: string[]; recommendations: string[]; overall_score: number }

// ── Chat ─────────────────────────────────────────────────────────
export interface Conversation { id: number; created_by: number; created_at: string; updated_at: string; is_active: boolean; participants: number[]; last_message?: Message }
export interface Message { id: number; conversation: number; sender: number; sender_email: string; sender_name: string; content: string; message_type: string; created_at: string; read_by: number[] }

// ── Investments ──────────────────────────────────────────────────
export interface InvestmentOpportunity { id: number; startup: number; startup_name?: string; investor: number; investor_email?: string; amount_requested: number | null; amount_offered: number | null; status: string; created_at: string }

// ── Meetings ─────────────────────────────────────────────────────
export interface Meeting { id: number; title: string; description: string; meeting_type: string; status: string; scheduled_start: string; scheduled_end: string; meeting_link: string; organizer: number; investor: number; startup: number | null; created_at: string }

// ── Notifications ────────────────────────────────────────────────
export interface Notification { id: number; type: string; title: string; message: string; is_read: boolean; data: Record<string, unknown>; created_at: string }

// ── Data Room ────────────────────────────────────────────────────
export interface DataRoom { id: number; startup: number; title: string; description: string; visibility: string; created_at: string }
export interface DataRoomDocument { id: number; data_room: number; title: string; document_type: string; file_size: number; created_at: string }

// ── Activity Feed ────────────────────────────────────────────────
export interface FeedActivity { id: number; actor: number; actor_email: string; activity_type: string; title: string; description: string; startup: number | null; investor: number | null; created_at: string; reaction_count?: number; comment_count?: number }

// ── Search ───────────────────────────────────────────────────────
export interface SearchResult<T> { count: number; next: string | null; previous: string | null; results: T[] }

// ── Billing ──────────────────────────────────────────────────────
export interface SubscriptionPlan { id: number; name: string; slug: string; tier: string; monthly_price: number; yearly_price: number; features: Record<string, boolean>; limits: Record<string, number>; is_popular: boolean }
export interface UserSubscription { id: number; plan: SubscriptionPlan; status: string; billing_cycle: string; start_date: string; end_date: string; auto_renew: boolean }
export interface Invoice { id: number; invoice_number: string; amount: number; status: string; plan_name: string; created_at: string }

// ── Analytics ────────────────────────────────────────────────────
export interface FounderDashboard { kpi_cards: Record<string, { value: number; growth?: number }>; funding_progress: { goal: number; raised: number; percentage: number } }
export interface InvestorDashboard { kpi_cards: Record<string, { value: number; growth?: number }>; deal_pipeline: Record<string, unknown>; meeting_stats: Record<string, unknown>; sector_distribution: { startup__industry: string; count: number; avg_score: number }[] }

// ── Admin ────────────────────────────────────────────────────────
export interface AdminDashboard { total_users: number; total_founders: number; total_investors: number; active_subscriptions: number; total_startups: number; active_deals: number; closed_deals: number; new_matches_30d: number; open_tickets: number }
export interface AuditLog { id: number; actor_email: string; action_type: string; target_type: string; target_repr: string; description: string; created_at: string }
export interface SupportTicket { id: number; user: number; user_email: string; subject: string; category: string; priority: string; status: string; assigned_to: number | null; created_at: string; updated_at: string }
export interface SupportMessage { id: number; ticket: number; sender: number; sender_email: string; content: string; is_internal: boolean; created_at: string }

// ── Observability ────────────────────────────────────────────────
export interface HealthCheck { status: string; detail: string }
export interface SystemMetrics { api: Record<string, unknown>; realtime: Record<string, unknown>; system: Record<string, unknown>; queue: Record<string, unknown> }
