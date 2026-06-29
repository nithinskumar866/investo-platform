"use client"

import { useInvestorAnalytics, useInvestorCharts } from "@/hooks/use-api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell
} from "recharts"
import { TrendingUp, Activity } from "lucide-react"

const COLORS = ["#6366f1", "#8b5cf6", "#ec4899", "#f59e0b", "#10b981", "#06b6d4", "#f97316"]

export default function AnalyticsPage() {
  const { data: analytics, isLoading: isAnalyticsLoading } = useInvestorAnalytics()
  const { data: charts, isLoading: isChartsLoading } = useInvestorCharts()

  const isLoading = isAnalyticsLoading || isChartsLoading

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64 mt-2" />
        </div>
        <div className="grid gap-6 md:grid-cols-2">
          <Skeleton className="h-80" />
          <Skeleton className="h-80" />
        </div>
      </div>
    )
  }

  const sectorData = analytics?.sector_distribution ?? []
  const kpiCards = analytics?.kpi_cards ?? {}
  
  // Maps backend charts to UI format
  const matchesTrend = charts?.daily_matches || []
  const viewsTrend = charts?.daily_views || []
  
  // We'll merge them into a single array for the Recharts line chart if they align, 
  // or just use matches for now
  const trendData = matchesTrend.map((m: any, i: number) => ({
    date: m.date,
    matches: m.count,
    views: viewsTrend[i]?.count || 0
  }))

  const pipeline: any = analytics?.deal_pipeline?.by_status || {}
  const funnelData = [
    { metric: "Interested", value: pipeline.interested || 0 },
    { metric: "Meetings", value: pipeline.meeting_scheduled || 0 },
    { metric: "Diligence", value: pipeline.due_diligence || 0 },
    { metric: "Term Sheets", value: pipeline.term_sheet_sent || 0 },
    { metric: "Closed", value: pipeline.invested || 0 },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
        <p className="text-muted-foreground">Track your investment performance and trends</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {[
          { label: "Matches", value: String(kpiCards.matches?.value ?? "0"), icon: Activity, color: "text-blue-500" },
          { label: "Deals Closed", value: String(kpiCards.invested_deals?.value ?? "0"), icon: TrendingUp, color: "text-emerald-500" },
          { label: "Response Rate", value: kpiCards.meeting_completion_rate?.value != null ? `${kpiCards.meeting_completion_rate.value}%` : "—", icon: TrendingUp, color: "text-amber-500" },
        ].map((item) => {
          const Icon = item.icon
          return (
            <Card key={item.label}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">{item.label}</CardTitle>
                <Icon className={`h-4 w-4 ${item.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{item.value}</div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Platform Activity Trends</CardTitle>
          </CardHeader>
          <CardContent>
            {trendData.length === 0 ? (
              <div className="flex h-[300px] items-center justify-center text-sm text-muted-foreground">
                No activity data available.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis dataKey="date" className="text-xs" tick={{ fontSize: 12 }} />
                  <YAxis className="text-xs" tick={{ fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "var(--radius)" }}
                  />
                  <Line type="monotone" dataKey="matches" stroke="#6366f1" strokeWidth={2} name="Matches" />
                  <Line type="monotone" dataKey="views" stroke="#10b981" strokeWidth={2} name="Views" />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Sector Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {sectorData.length === 0 ? (
              <div className="flex h-[300px] items-center justify-center text-sm text-muted-foreground">
                No sector data available yet.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={sectorData}
                    dataKey="count"
                    nameKey="startup__industry"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={({ startup__industry, percent }) =>
                      `${startup__industry} ${(percent * 100).toFixed(0)}%`
                    }
                  >
                    {sectorData.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Deal Pipeline Funnel</CardTitle>
        </CardHeader>
        <CardContent>
          {funnelData.every(d => d.value === 0) ? (
            <div className="flex h-[250px] items-center justify-center text-sm text-muted-foreground">
              No deals in pipeline.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={funnelData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis dataKey="metric" className="text-xs" tick={{ fontSize: 12 }} />
                <YAxis className="text-xs" tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "var(--radius)" }}
                />
                <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
