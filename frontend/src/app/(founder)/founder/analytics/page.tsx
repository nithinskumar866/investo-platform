"use client"

import { useFounderAnalytics } from "@/hooks/use-api"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { TrendingUp, TrendingDown, Eye, Handshake, CalendarCheck, DollarSign } from "lucide-react"
import { formatCurrency } from "@/lib/utils"

function StatCard({ label, value, growth, icon: Icon }: { label: string; value: number; growth?: number; icon: React.ElementType }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2">
          <span className="text-2xl font-bold">{value}</span>
          {growth !== undefined && (
            <span className={`flex items-center text-xs ${growth >= 0 ? "text-emerald-500" : "text-destructive"}`}>
              {growth >= 0 ? <TrendingUp className="h-3 w-3 mr-0.5" /> : <TrendingDown className="h-3 w-3 mr-0.5" />}
              {Math.abs(growth)}%
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export default function AnalyticsPage() {
  const { data: analytics, isLoading } = useFounderAnalytics(1)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
        <p className="text-muted-foreground">Track your startup&apos;s performance metrics</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total Views" value={analytics?.kpi_cards?.total_views?.value ?? 0} growth={analytics?.kpi_cards?.total_views?.growth} icon={Eye} />
        <StatCard label="Matches" value={analytics?.kpi_cards?.matches?.value ?? 0} growth={analytics?.kpi_cards?.matches?.growth} icon={Handshake} />
        <StatCard label="Meetings" value={analytics?.kpi_cards?.meetings?.value ?? 0} growth={analytics?.kpi_cards?.meetings?.growth} icon={CalendarCheck} />
        <StatCard label="Investments" value={analytics?.kpi_cards?.investments?.value ?? 0} growth={analytics?.kpi_cards?.investments?.growth} icon={DollarSign} />
      </div>

      {analytics?.funding_progress && (
        <Card>
          <CardHeader>
            <CardTitle>Funding Progress</CardTitle>
            <CardDescription>Amount raised vs. funding goal</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between text-sm mb-2">
              <span>Raised: {formatCurrency(analytics.funding_progress.raised)}</span>
              <span>Goal: {formatCurrency(analytics.funding_progress.goal)}</span>
            </div>
            <div className="h-3 w-full rounded-full bg-primary/20">
              <div
                className="h-3 rounded-full bg-primary transition-all"
                style={{ width: `${Math.min(analytics.funding_progress.percentage, 100)}%` }}
              />
            </div>
            <p className="text-sm text-muted-foreground mt-2">{analytics.funding_progress.percentage}% of funding goal achieved</p>
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader><Skeleton className="h-5 w-40" /></CardHeader>
              <CardContent><Skeleton className="h-40 w-full" /></CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle>Views Over Time</CardTitle>
              <CardDescription>Profile view trends</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-end justify-between h-40 gap-1">
                {[40, 65, 45, 80, 55, 90, 70, 95, 60, 85, 75, 100].map((h, i) => (
                  <div key={i} className="flex-1 flex flex-col items-center gap-1">
                    <div
                      className="w-full rounded-md bg-primary/80 transition-all hover:bg-primary"
                      style={{ height: `${h}%` }}
                    />
                    <span className="text-[10px] text-muted-foreground">
                      {["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][i]}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Match Rate</CardTitle>
              <CardDescription>Investor match score distribution</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                { label: "90-100%", value: 15, color: "bg-emerald-500" },
                { label: "70-89%", value: 30, color: "bg-emerald-400" },
                { label: "50-69%", value: 25, color: "bg-amber-400" },
                { label: "Below 50%", value: 30, color: "bg-muted" },
              ].map((item) => (
                <div key={item.label}>
                  <div className="flex justify-between text-sm mb-1">
                    <span>{item.label}</span>
                    <span className="text-muted-foreground">{item.value}%</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-primary/10">
                    <div className={`h-2 rounded-full ${item.color}`} style={{ width: `${item.value}%` }} />
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Meeting Conversion Funnel</CardTitle>
              <CardDescription>Match → Intro → Meeting → Deal</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {[
                { stage: "Matches", count: analytics?.kpi_cards?.matches?.value ?? 0, pct: 100 },
                { stage: "Intros", count: Math.round((analytics?.kpi_cards?.matches?.value ?? 0) * 0.6), pct: 60 },
                { stage: "Meetings", count: analytics?.kpi_cards?.meetings?.value ?? 0, pct: 35 },
                { stage: "Deals", count: analytics?.kpi_cards?.investments?.value ?? 0, pct: 15 },
              ].map((step) => (
                <div key={step.stage}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="font-medium">{step.stage}</span>
                    <span className="text-muted-foreground">{step.count}</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-primary/10">
                    <div
                      className="h-2 rounded-full bg-primary transition-all"
                      style={{ width: `${step.pct}%` }}
                    />
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
