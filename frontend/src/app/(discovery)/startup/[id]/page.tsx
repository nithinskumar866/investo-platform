"use client"

import { useState } from "react"
import Link from "next/link"
import { useParams, useRouter } from "next/navigation"
import { toast } from "sonner"
import {
  BadgeCheck, Bookmark, Calendar, FolderLock, Globe, Loader2, MapPin, MessageSquare, Pencil, Sparkles, Users,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Field } from "@/components/ui/field"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog"
import { MeetingDialog } from "@/components/meetings/meeting-dialog"
import {
  useExpressInterest, useFundingProgress, useInvestorDeals, useInvestorRooms, useMatches,
  useMyStartups, usePublishStartup, useRequestRoomAccess, useSaveMatch, useStartup,
} from "@/hooks/use-api"
import { useAuthStore } from "@/stores/auth"
import { dealStageLabel, humanize, industryLabel, stageLabel } from "@/lib/constants"
import { formatCurrency, getInitials } from "@/lib/utils"
import { Avatar } from "@/components/ui/avatar"
import type { StartupDetail } from "@/types/api"

function FundingBar({ id, currency }: { id: number; currency: string }) {
  const { data, isLoading } = useFundingProgress(id)
  if (isLoading) return <Skeleton className="h-24 w-full" />
  if (!data) return null
  const pct = Math.min(data.percent_raised, 100)
  return (
    <Card data-testid="funding-progress">
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Funding progress</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <Progress value={pct} aria-label="Percent of funding goal raised" />
        <div className="flex flex-wrap justify-between gap-2 text-sm">
          <span data-testid="funding-raised">{formatCurrency(data.raised, currency)} raised</span>
          <span className="text-muted-foreground">{data.goal ? `of ${formatCurrency(data.goal, currency)} goal` : "No goal set"}</span>
        </div>
        <p className="text-xs text-muted-foreground">
          {data.percent_raised}% raised &middot; {formatCurrency(data.committed, currency)} committed &middot; {data.investor_count} investor{data.investor_count === 1 ? "" : "s"} &middot; dummy money
        </p>
      </CardContent>
    </Card>
  )
}

function ExpressInterestDialog({ startup, onClose }: { startup: StartupDetail; onClose: () => void }) {
  const expressInterest = useExpressInterest()
  const [amount, setAmount] = useState(startup.funding_goal ? String(Number(startup.funding_goal)) : "")
  const [notes, setNotes] = useState("")
  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent>
        <DialogTitle>Express interest in {startup.name}</DialogTitle>
        <DialogDescription>This adds a deal to your pipeline and notifies the founder. Dummy money only.</DialogDescription>
        <form
          className="space-y-3"
          onSubmit={(e) => {
            e.preventDefault()
            expressInterest.mutate(
              { startup_id: startup.id, amount_requested: amount || undefined, notes: notes.trim() },
              {
                onSuccess: () => {
                  toast.success("Interest sent. The deal is now in your pipeline.")
                  onClose()
                },
              },
            )
          }}
        >
          <Field label="Amount of interest ($)"><Input type="number" min="0" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} /></Field>
          <Field label="Note to founder (optional)"><Textarea value={notes} onChange={(e) => setNotes(e.target.value)} /></Field>
          <Button type="submit" className="w-full" disabled={expressInterest.isPending}>
            {expressInterest.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Send interest
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function DataRoomAccess({ startupId }: { startupId: number }) {
  const { data: rooms, isLoading } = useInvestorRooms(startupId)
  const request = useRequestRoomAccess()

  return (
    <Card data-testid="data-room-access">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base"><FolderLock className="h-4 w-4" /> Data room</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading ? (
          <Skeleton className="h-12 w-full" />
        ) : !rooms?.length ? (
          <p className="text-sm text-muted-foreground">This startup has not opened a data room yet.</p>
        ) : (
          rooms.map((room) => (
            <div key={room.id} className="space-y-2 rounded-lg border p-3">
              <p className="text-sm font-medium">{room.title}</p>
              {room.description && <p className="text-xs text-muted-foreground">{room.description}</p>}
              {room.access_status === "none" && (
                <Button size="sm" className="w-full" disabled={request.isPending}
                  onClick={() => request.mutate({ id: room.id }, { onSuccess: () => toast.success("Access requested. The founder will review it.") })}>
                  Request access
                </Button>
              )}
              {room.access_status === "pending" && <Badge variant="warning">Access requested, awaiting founder</Badge>}
              {room.access_status === "denied" && <Badge variant="destructive">Access denied</Badge>}
              {room.access_status === "approved" && (
                <Button size="sm" variant="outline" className="w-full" asChild>
                  <Link href="/investor/data-room">View documents</Link>
                </Button>
              )}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  )
}

function InvestorActions({ startup }: { startup: StartupDetail }) {
  const router = useRouter()
  const { data: deals } = useInvestorDeals()
  const { data: matches } = useMatches("startup")
  const save = useSaveMatch()
  const [dialog, setDialog] = useState<"interest" | "meeting" | null>(null)

  const deal = deals?.find((d) => d.startup.id === startup.id)
  const match = matches?.find((m) => m.startup_id === startup.id)

  return (
    <Card>
      <CardHeader className="pb-3"><CardTitle className="text-base">Actions</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {deal ? (
          <Button variant="outline" className="w-full" asChild>
            <Link href="/investor/deals">In pipeline: {dealStageLabel(deal.status)}</Link>
          </Button>
        ) : (
          <Button className="w-full" onClick={() => setDialog("interest")}>Express interest</Button>
        )}
        {match ? (
          <>
            <Button variant="outline" className="w-full" onClick={() => router.push(`/chat?participant=${match.startup_owner_id}`)}>
              <MessageSquare className="mr-2 h-4 w-4" /> Message founder
            </Button>
            <Button variant="outline" className="w-full" onClick={() => setDialog("meeting")}>
              <Calendar className="mr-2 h-4 w-4" /> Request meeting
            </Button>
            <Button variant="outline" className="w-full" asChild>
              <Link href={`/investor/insights?match=${match.id}`}><Sparkles className="mr-2 h-4 w-4" /> Explain this match</Link>
            </Button>
            <Button variant="ghost" className="w-full" disabled={match.is_bookmarked || match.status === "saved" || save.isPending}
              onClick={() => save.mutate(match.id, { onSuccess: () => toast.success("Saved") })}>
              <Bookmark className="mr-2 h-4 w-4" /> {match.is_bookmarked || match.status === "saved" ? "Saved" : "Save startup"}
            </Button>
          </>
        ) : (
          <p className="text-xs text-muted-foreground">
            Messaging and meeting requests open once you are matched with this startup.
          </p>
        )}
      </CardContent>
      {dialog === "interest" && <ExpressInterestDialog startup={startup} onClose={() => setDialog(null)} />}
      <MeetingDialog open={dialog === "meeting"} onOpenChange={() => setDialog(null)} match={match} />
    </Card>
  )
}

function OwnerActions({ startup }: { startup: StartupDetail }) {
  const publish = usePublishStartup()
  return (
    <Card>
      <CardHeader className="pb-3"><CardTitle className="text-base">Your startup</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {startup.status === "draft" && (
          <Button className="w-full" disabled={publish.isPending}
            onClick={() => publish.mutate(startup.id, { onSuccess: () => toast.success("Published") })}>
            Publish
          </Button>
        )}
        <Button variant="outline" className="w-full" asChild>
          <Link href={`/founder/startups/${startup.id}/edit`}><Pencil className="mr-2 h-4 w-4" /> Edit and documents</Link>
        </Button>
        <Button variant="outline" className="w-full" asChild><Link href="/founder/data-room">Manage data room</Link></Button>
        <Button variant="outline" className="w-full" asChild><Link href="/founder/deals">View deals</Link></Button>
      </CardContent>
    </Card>
  )
}

function Fact({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm font-medium">{value}</p>
    </div>
  )
}

export default function StartupDetailPage() {
  const id = Number(useParams<{ id: string }>().id)
  const role = useAuthStore((s) => s.user?.role)
  const { data: startup, isLoading, error } = useStartup(id)
  const { data: mine } = useMyStartups(role === "entrepreneur")

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-72" />
        <div className="grid gap-6 lg:grid-cols-3">
          <Skeleton className="h-96 lg:col-span-2" />
          <Skeleton className="h-96" />
        </div>
      </div>
    )
  }

  if (error || !startup) {
    return (
      <div className="py-20 text-center">
        <h1 className="text-xl font-semibold">Startup not found</h1>
        <p className="mt-2 text-muted-foreground">It may be unpublished, or the link is wrong.</p>
        <Button asChild variant="outline" className="mt-4"><Link href="/">Back to dashboard</Link></Button>
      </div>
    )
  }

  const isOwner = !!mine?.some((s) => s.id === startup.id)
  const currency = startup.currency || "USD"
  const m = startup.metrics
  const metrics = m ? ([
    ["Monthly revenue", m.monthly_revenue !== null ? formatCurrency(m.monthly_revenue, currency) : null],
    ["Annual revenue", m.annual_revenue !== null ? formatCurrency(m.annual_revenue, currency) : null],
    ["Revenue growth", m.revenue_growth_pct !== null ? `${Number(m.revenue_growth_pct)}%` : null],
    ["Monthly active users", m.monthly_active_users],
    ["Total users", m.total_users],
    ["Gross margin", m.gross_margin_pct !== null ? `${Number(m.gross_margin_pct)}%` : null],
    ["Burn rate", m.burn_rate !== null ? formatCurrency(m.burn_rate, currency) : null],
    ["Runway", m.runway_months !== null ? `${m.runway_months} months` : null],
  ] as const).filter(([, v]) => v !== null && v !== undefined) : []

  return (
    <div className="space-y-6">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-2xl font-bold tracking-tight">{startup.name}</h1>
          {startup.is_verified && <Badge variant="success" className="gap-1"><BadgeCheck className="h-3 w-3" /> Verified</Badge>}
          {startup.status !== "active" && <Badge variant="secondary" className="capitalize">{startup.status}</Badge>}
        </div>
        <p className="mt-1 text-muted-foreground">{startup.tagline}</p>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
          <Badge variant="secondary">{industryLabel(startup.industry)}</Badge>
          <Badge variant="outline">{stageLabel(startup.stage)}</Badge>
          {startup.location && <span className="flex items-center gap-1"><MapPin className="h-3.5 w-3.5" /> {startup.location}</span>}
          {startup.website && (
            <a href={startup.website} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 hover:underline"><Globe className="h-3.5 w-3.5" /> Website</a>
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader className="pb-3"><CardTitle className="text-base">About</CardTitle></CardHeader>
            <CardContent className="space-y-3 text-sm">
              {startup.short_description && <p>{startup.short_description}</p>}
              {startup.description && <p className="whitespace-pre-line text-muted-foreground">{startup.description}</p>}
              {startup.detailed_pitch && <p className="whitespace-pre-line text-muted-foreground">{startup.detailed_pitch}</p>}
              {!startup.short_description && !startup.description && !startup.detailed_pitch && (
                <p className="text-muted-foreground">The founder has not added a description yet.</p>
              )}
              <div className="grid grid-cols-2 gap-4 border-t pt-4 sm:grid-cols-3">
                <Fact label="Founder" value={startup.owner_name} />
                <Fact label="Funding goal" value={startup.funding_goal ? formatCurrency(startup.funding_goal, currency) : "Not set"} />
                <Fact label="Equity offered" value={startup.equity_offered ? `${Number(startup.equity_offered)}%` : "Not set"} />
                <Fact label="Valuation" value={startup.valuation ? formatCurrency(startup.valuation, currency) : "Not set"} />
                <Fact label="Team size" value={startup.team_size ?? "Not set"} />
                <Fact label="Business model" value={<span className="capitalize">{humanize(startup.business_model) || "Not set"}</span>} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3"><CardTitle className="flex items-center gap-2 text-base"><Users className="h-4 w-4" /> Team</CardTitle></CardHeader>
            <CardContent>
              {!startup.team_members?.length ? (
                <p className="text-sm text-muted-foreground">No team members listed.</p>
              ) : (
                <ul className="grid gap-3 sm:grid-cols-2">
                  {startup.team_members.map((member) => (
                    <li key={member.id ?? member.name} className="flex items-center gap-3">
                      <Avatar fallback={getInitials(member.name)} />
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium">{member.name}</p>
                        <p className="truncate text-xs text-muted-foreground">{member.role}</p>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3"><CardTitle className="text-base">Metrics</CardTitle></CardHeader>
            <CardContent>
              {metrics.length === 0 && !m?.traction_description ? (
                <p className="text-sm text-muted-foreground">No metrics shared yet.</p>
              ) : (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                    {metrics.map(([label, value]) => <Fact key={label} label={label} value={String(value)} />)}
                  </div>
                  {m?.traction_description && <p className="text-sm text-muted-foreground">{m.traction_description}</p>}
                </div>
              )}
            </CardContent>
          </Card>

          {!!startup.funding_rounds?.length && (
            <Card>
              <CardHeader className="pb-3"><CardTitle className="text-base">Past funding rounds</CardTitle></CardHeader>
              <CardContent>
                <ul className="divide-y">
                  {startup.funding_rounds.map((r) => (
                    <li key={r.id} className="flex justify-between py-2 text-sm">
                      <span>{r.round_name}</span>
                      <span className="text-muted-foreground">{r.amount ? formatCurrency(r.amount, currency) : "Undisclosed"}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-6">
          {role === "investor" && <InvestorActions startup={startup} />}
          {isOwner && <OwnerActions startup={startup} />}
          <FundingBar id={startup.id} currency={currency} />
          {role === "investor" && <DataRoomAccess startupId={startup.id} />}
        </div>
      </div>
    </div>
  )
}
