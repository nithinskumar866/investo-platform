"use client"

import { useInvestorAnalytics } from "@/hooks/use-api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from "recharts"
import { TrendingUp, PieChartIcon, Activity } from "lucide-react"

const COLORS = ["#6366f1", "#8b5cf6", "#ec4899", "#f59e0b", "#10b981", "#06b6d4", "#f97316"]

const mockTrendData = [
  { month: "Jan", deals: 4, meetings: 2 },
  { month: "Feb", deals: 6, meetings: 3 },
  { month: "Mar", deals: 8, meetings: 5 },
  { month: "Apr", deals: 7, meetings: 4 },
  { month: "May", deals: 10, meetings: 6 },
  { month: "Jun", deals: 12, meetings: 8 },
]

export default function AnalyticsPage() {
  const { data: analytics, isLoading } = useInvestorAnalytics()

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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
        <p className="text-muted-foreground">Track your investment performance and trends</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {[
          { label: "Avg Match Score", value: "72%", icon: Activity, color: "text-blue-500" },
          { label: "Deals Closed", value: String((kpiCards.closed_deals as any)?.value ?? kpiCards.closed_deals ?? "0"), icon: TrendingUp, color: "text-emerald-500" },
          { label: "Response Rate", value: (kpiCards.response_rate as any)?.value ? `${(kpiCards.response_rate as any).value}%` : kpiCards.response_rate ? `${kpiCards.response_rate}%` : "—", icon: TrendingUp, color: "text-amber-500" },
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
            <CardTitle className="text-sm font-medium">Deal Flow Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={mockTrendData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis dataKey="month" className="text-xs" tick={{ fontSize: 12 }} />
                <YAxis className="text-xs" tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "var(--radius)" }}
                />
                <Line type="monotone" dataKey="deals" stroke="#6366f1" strokeWidth={2} name="Deals" />
                <Line type="monotone" dataKey="meetings" stroke="#10b981" strokeWidth={2} name="Meetings" />
              </LineChart>
            </ResponsiveContainer>
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
          <CardTitle className="text-sm font-medium">Response Rate Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart
              data={[
                { metric: "Contacted", value: 24 },
                { metric: "Responded", value: 16 },
                { metric: "Meetings", value: 10 },
                { metric: "Term Sheets", value: 5 },
                { metric: "Closed", value: 3 },
              ]}
            >
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis dataKey="metric" className="text-xs" tick={{ fontSize: 12 }} />
              <YAxis className="text-xs" tick={{ fontSize: 12 }} />
              <Tooltip
                contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "var(--radius)" }}
              />
              <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}
