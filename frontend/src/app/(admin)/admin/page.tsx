"use client"

import {
  Card, CardHeader, CardTitle, CardDescription, CardContent,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { useAdminDashboard } from "@/hooks/use-api"
import { Users, Building2, TrendingUp, DollarSign, Ticket, ArrowUp, ArrowDown } from "lucide-react"

const metricCards = [
  { key: "total_users", label: "Total Users", icon: Users },
  { key: "total_startups", label: "Startups", icon: Building2 },
  { key: "active_deals", label: "Active Deals", icon: TrendingUp },
  { key: "total_investors", label: "Investors", icon: DollarSign },
]

export default function AdminDashboardPage() {
  const { data, isLoading } = useAdminDashboard()

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
          <Skeleton className="h-80 lg:col-span-2" />
          <Skeleton className="h-80" />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Admin Dashboard</h1>
        <p className="text-muted-foreground">Platform overview and key metrics</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metricCards.map(({ key, label, icon: Icon }) => (
          <Card key={key}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
              <Icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{data?.[key as keyof typeof data] ?? 0}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Recent Users</CardTitle>
            <CardDescription>Latest registered accounts</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { name: "John Doe", email: "john@example.com", role: "entrepreneur", date: "2m ago" },
                { name: "Jane Smith", email: "jane@example.com", role: "investor", date: "5m ago" },
                { name: "Bob Johnson", email: "bob@example.com", role: "entrepreneur", date: "12m ago" },
                { name: "Alice Brown", email: "alice@example.com", role: "investor", date: "1h ago" },
              ].map((u, i) => (
                <div key={i} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{u.name}</p>
                    <p className="text-xs text-muted-foreground">{u.email}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={u.role === "investor" ? "warning" : "default"}>{u.role}</Badge>
                    <span className="text-xs text-muted-foreground">{u.date}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Ticket Queue</CardTitle>
            <CardDescription>Open support tickets</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { subject: "Payment issue", priority: "high", status: "open" },
              { subject: "Account verification", priority: "medium", status: "in_progress" },
              { subject: "Feature request", priority: "low", status: "open" },
            ].map((t, i) => (
              <div key={i} className="flex items-center justify-between">
                <p className="text-sm">{t.subject}</p>
                <div className="flex gap-1">
                  <Badge variant={t.priority === "high" ? "destructive" : t.priority === "medium" ? "warning" : "default"}>
                    {t.priority}
                  </Badge>
                  <Badge variant={t.status === "open" ? "default" : "secondary"}>
                    {t.status.replace("_", " ")}
                  </Badge>
                </div>
              </div>
            ))}
            <div className="flex items-center justify-between pt-2 text-sm">
              <span className="text-muted-foreground">{data?.open_tickets ?? 0} open tickets</span>
              <span className="font-medium text-primary">{data?.new_matches_30d ?? 0} new matches</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
