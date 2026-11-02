"use client"

import Link from "next/link"
import { useInvestorAnalytics, useInvestorDeals, useMatches } from "@/hooks/use-api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Activity, Bookmark, Building2, ChevronRight, DollarSign, UserCheck } from "lucide-react"
import { DEAL_STAGES } from "@/lib/constants"

const kpiConfig = [
  { key: "matches", label: "Matches", icon: UserCheck, color: "text-blue-500" },
  { key: "saved_startups", label: "Saved Startups", icon: Bookmark, color: "text-violet-500" },
  { key: "deal_pipeline_total", label: "Deals in Pipeline", icon: Activity, color: "text-amber-500" },
  { key: "invested_deals", label: "Closed Investments", icon: DollarSign, color: "text-emerald-500" },
]

export default function InvestorDashboard() {
  const { data: analytics, isLoading: aLoading } = useInvestorAnalytics()
  const { data: matches, isLoading: mLoading } = useMatches("startup")
  const { data: deals } = useInvestorDeals()

  if (aLoading || mLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24" />)}
        </div>
      </div>
    )
  }

  const kpiCards = analytics?.kpi_cards ?? {}
  const topMatches = (matches ?? []).slice(0, 5)
  const total = deals?.length ?? 0

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Investor Dashboard</h1>
        <p className="text-muted-foreground">Overview of your investment activity</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {kpiConfig.map(({ key, label, icon: Icon, color }) => (
          <Card key={key}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
              <Icon className={`h-4 w-4 ${color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold" data-testid={`kpi-${key}`}>{kpiCards[key]?.value ?? 0}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Top Matches</CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/investor/matches">View All <ChevronRight className="ml-1 h-4 w-4" /></Link>
            </Button>
          </CardHeader>
          <CardContent>
            {topMatches.length === 0 ? (
              <p className="text-sm text-muted-foreground">No matches found yet.</p>
            ) : (
              <div className="space-y-3">
                {topMatches.map((m) => (
                  <Link key={m.id} href={`/startup/${m.startup_id}`} className="flex items-center justify-between gap-2 rounded-lg border p-3 hover:bg-accent/10">
                    <div className="flex min-w-0 items-center gap-3">
                      <Building2 className="h-8 w-8 shrink-0 rounded-lg bg-primary/10 p-1.5 text-primary" />
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium">{m.startup_name}</p>
                        <p className="truncate text-xs text-muted-foreground">{m.startup_tagline}</p>
                      </div>
                    </div>
                    <Badge variant={m.score >= 80 ? "success" : m.score >= 50 ? "warning" : "secondary"} className="shrink-0">
                      {Math.round(m.score)}% Match
                    </Badge>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Pipeline Summary</CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/investor/deals">Open <ChevronRight className="ml-1 h-4 w-4" /></Link>
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {DEAL_STAGES.map((stage) => {
              const count = (deals ?? []).filter((d) => d.status === stage.value).length
              return (
                <div key={stage.value} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span>{stage.label}</span>
                    <span className="text-muted-foreground">{count}</span>
                  </div>
                  <Progress value={total ? (count / total) * 100 : 0} className="h-1.5" aria-label={stage.label} />
                </div>
              )
            })}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
