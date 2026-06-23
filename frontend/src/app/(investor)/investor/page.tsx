"use client"

import { useInvestorAnalytics, useMatches, useStartups } from "@/hooks/use-api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { formatCurrency } from "@/lib/utils"
import {
  TrendingUp, DollarSign, Calendar, Activity, ArrowUpRight,
  Building2, UserCheck, ChevronRight,
} from "lucide-react"
import Link from "next/link"

const kpiConfig: Record<string, { label: string; icon: typeof TrendingUp; format?: (v: number) => string; color: string }> = {
  deal_flow: { label: "Deal Flow", icon: Activity, color: "text-blue-500" },
  portfolio_size: { label: "Portfolio Size", icon: DollarSign, format: (v) => formatCurrency(v), color: "text-emerald-500" },
  meetings_this_week: { label: "Meetings This Week", icon: Calendar, color: "text-violet-500" },
  response_rate: { label: "Response Rate", icon: TrendingUp, format: (v) => `${v}%`, color: "text-amber-500" },
}

export default function InvestorDashboard() {
  const { data: analytics, isLoading: aLoading } = useInvestorAnalytics()
  const { data: matches, isLoading: mLoading } = useMatches("startup")
  const { data: startups, isLoading: sLoading } = useStartups({ status: "verified" })

  if (aLoading || mLoading || sLoading) return <DashboardSkeleton />

  const kpiCards = analytics?.kpi_cards ?? {}
  const topMatches = (matches ?? []).slice(0, 5)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Investor Dashboard</h1>
        <p className="text-muted-foreground">Overview of your investment activity</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Object.entries(kpiConfig).map(([key, cfg]) => {
          const item = kpiCards[key] ?? { value: 0, growth: 0 }
          const Icon = cfg.icon
          const display = cfg.format ? cfg.format(item.value) : item.value
          return (
            <Card key={key}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">{cfg.label}</CardTitle>
                <Icon className={`h-4 w-4 ${cfg.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{display}</div>
                {item.growth !== undefined && (
                  <p className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
                    <ArrowUpRight className="h-3 w-3 text-emerald-500" />
                    <span className="text-emerald-500">{item.growth}%</span> vs last month
                  </p>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Matches</CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/investor/matches">
                View All <ChevronRight className="ml-1 h-4 w-4" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            {topMatches.length === 0 ? (
              <p className="text-sm text-muted-foreground">No matches found yet.</p>
            ) : (
              <div className="space-y-3">
                {topMatches.map((m) => (
                  <div key={m.id} className="flex items-center justify-between rounded-lg border p-3">
                    <div className="flex items-center gap-3">
                      <Building2 className="h-8 w-8 rounded-lg bg-primary/10 p-1.5 text-primary" />
                      <div>
                        <p className="text-sm font-medium">{m.startup_detail?.name ?? `Startup #${m.startup}`}</p>
                        <p className="text-xs text-muted-foreground">{m.startup_detail?.tagline}</p>
                      </div>
                    </div>
                    <Badge variant={m.score >= 80 ? "success" : m.score >= 50 ? "warning" : "secondary"}>
                      {Math.round(m.score)}% Match
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Pipeline Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {["Lead", "Intro", "Meeting", "Term Sheet", "Closed"].map((stage) => {
              const count = 0
              return (
                <div key={stage} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span>{stage}</span>
                    <span className="text-muted-foreground">{count}</span>
                  </div>
                  <Progress value={0} className="h-1.5" />
                </div>
              )
            })}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div>
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-48 mt-2" />
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-8 w-16 mt-2" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
