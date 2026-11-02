// Mirrors the TextChoices in apps/startups/models.py and apps/data_room/models.py.
export const INDUSTRIES = [
  { value: "ai_ml", label: "Artificial Intelligence / ML" },
  { value: "fintech", label: "Fintech" },
  { value: "healthtech", label: "Healthtech" },
  { value: "edtech", label: "Edtech" },
  { value: "saas", label: "SaaS / Cloud" },
  { value: "ecommerce", label: "E-commerce" },
  { value: "marketplace", label: "Marketplace" },
  { value: "social", label: "Social Media" },
  { value: "gaming", label: "Gaming" },
  { value: "cleantech", label: "Cleantech" },
  { value: "biotech", label: "Biotech" },
  { value: "blockchain", label: "Blockchain / Web3" },
  { value: "real_estate", label: "Real Estate / PropTech" },
  { value: "transport", label: "Transport / Mobility" },
  { value: "food_tech", label: "Food Tech" },
  { value: "travel", label: "Travel / Hospitality" },
  { value: "cybersecurity", label: "Cybersecurity" },
  { value: "iot", label: "IoT / Hardware" },
  { value: "media", label: "Media / Entertainment" },
  { value: "other", label: "Other" },
]

export const STAGES = [
  { value: "idea", label: "Idea / Concept" },
  { value: "pre_seed", label: "Pre-Seed" },
  { value: "seed", label: "Seed" },
  { value: "series_a", label: "Series A" },
  { value: "series_b", label: "Series B" },
  { value: "series_c", label: "Series C+" },
  { value: "growth", label: "Growth Stage" },
]

export const BUSINESS_MODELS = [
  { value: "b2b", label: "B2B" },
  { value: "b2c", label: "B2C" },
  { value: "b2b2c", label: "B2B2C" },
  { value: "marketplace", label: "Marketplace" },
  { value: "subscription", label: "Subscription" },
  { value: "freemium", label: "Freemium" },
  { value: "advertising", label: "Advertising" },
  { value: "hardware", label: "Hardware" },
  { value: "other", label: "Other" },
]

export const STARTUP_DOCUMENT_TYPES = [
  { value: "pitch_deck", label: "Pitch Deck" },
  { value: "business_plan", label: "Business Plan" },
  { value: "financial_model", label: "Financial Model" },
  { value: "market_analysis", label: "Market Analysis" },
  { value: "term_sheet", label: "Term Sheet" },
  { value: "other", label: "Other" },
]

export const DATA_ROOM_DOCUMENT_TYPES = [
  { value: "pitch_deck", label: "Pitch Deck" },
  { value: "financials", label: "Financials" },
  { value: "cap_table", label: "Cap Table" },
  { value: "business_plan", label: "Business Plan" },
  { value: "legal", label: "Legal" },
  { value: "traction_report", label: "Traction Report" },
  { value: "product_demo", label: "Product Demo" },
  { value: "market_research", label: "Market Research" },
  { value: "other", label: "Other" },
]

export const MEETING_TYPES = [
  { value: "intro_call", label: "Intro Call" },
  { value: "pitch_meeting", label: "Pitch Meeting" },
  { value: "due_diligence", label: "Due Diligence" },
  { value: "negotiation", label: "Negotiation" },
  { value: "follow_up", label: "Follow Up" },
]

export const DEAL_STAGES = [
  { value: "interested", label: "Interested" },
  { value: "meeting_scheduled", label: "Meeting Scheduled" },
  { value: "due_diligence", label: "Due Diligence" },
  { value: "negotiating", label: "Negotiating" },
  { value: "term_sheet_sent", label: "Term Sheet Sent" },
  { value: "invested", label: "Invested" },
]

const lookup = (list: { value: string; label: string }[]) => (value?: string | null) =>
  list.find((o) => o.value === value)?.label ?? (value ?? "").replace(/_/g, " ")

export const industryLabel = lookup(INDUSTRIES)
export const stageLabel = lookup(STAGES)
export const dealStageLabel = lookup([...DEAL_STAGES, { value: "rejected", label: "Rejected" }, { value: "withdrawn", label: "Withdrawn" }])
export const humanize = (value?: string | null) => (value ?? "").replace(/[_-]/g, " ")
