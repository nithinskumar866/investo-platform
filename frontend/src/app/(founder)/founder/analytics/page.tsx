"use client"

import { useFounderAnalytics, useFounderCharts, useFounderFunnel } from "@/hooks/use-api"
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
  const { data: analytics, isLoading: isAnalyticsLoading } = useFounderAnalytics()
  const { data: charts, isLoading: isChartsLoading } = useFounderCharts()
  const { data: funnel, isLoading: isFunnelLoading } = useFounderFunnel()

  const isLoading = isAnalyticsLoading || isChartsLoading || isFunnelLoading

  // Backend should return arrays like { date: string, count: number } for daily_views
  // Let's normalize it to exactly 12 bars for our simple UI visualization.
  const chartViews = charts?.daily_views || []
  
  // Funnel should map from backend to UI
  const meetingFunnel = funnel?.meeting_funnel || {}
  const funnelSteps = [
    { stage: "Matches", count: meetingFunnel.matches?.count || 0, pct: meetingFunnel.matches?.pct || 0 },
    { stage: "Intros", count: meetingFunnel.intros?.count || 0, pct: meetingFunnel.intros?.pct || 0 },
    { stage: "Meetings", count: meetingFunnel.meetings?.count || 0, pct: meetingFunnel.meetings?.pct || 0 },
  ]

  // Mock match rates until backend supports it
  // Wait, backend matches return match trends?
  // Let's use the actual daily_matches from charts
  const matchTrends = charts?.daily_matches || []

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
              {chartViews.length === 0 ? (
                <div className="flex items-center justify-center h-40 text-sm text-muted-foreground">
                  No view data available
                </div>
              ) : (
                <div className="flex flex-col gap-2 h-40 overflow-y-auto">
                  {chartViews.map((item: any, i: number) => (
                    <div key={i} className="flex items-center justify-between text-sm">
                      <span className="w-24 truncate">{item.date}</span>
                      <div className="flex-1 mx-2 h-2 rounded-full bg-primary/20">
                        <div className="h-2 rounded-full bg-primary" style={{ width: `${Math.min(item.count * 10, 100)}%` }} />
                      </div>
                      <span className="w-8 text-right font-medium">{item.count}</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Matches Over Time</CardTitle>
              <CardDescription>Investor match trends</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 h-40 overflow-y-auto">
              {matchTrends.length === 0 ? (
                <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
                  No match data available
                </div>
              ) : (
                matchTrends.map((item: any, i: number) => (
                  <div key={i}>
                    <div className="flex justify-between text-sm mb-1">
                      <span>{item.date}</span>
                      <span className="text-muted-foreground">{item.count} matches</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-primary/10">
                      <div className="h-2 rounded-full bg-emerald-500" style={{ width: `${Math.min(item.count * 10, 100)}%` }} />
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Meeting Conversion Funnel</CardTitle>
              <CardDescription>Match → Intro → Meeting</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {funnelSteps.map((step) => (
                <div key={step.stage}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="font-medium">{step.stage}</span>
                    <span className="text-muted-foreground">{step.count} ({step.pct}%)</span>
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
