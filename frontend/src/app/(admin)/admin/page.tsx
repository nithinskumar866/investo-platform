"use client"

import {
  Card, CardHeader, CardTitle, CardDescription, CardContent,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { useAdminDashboard, useAdminUsers, useAdminTickets } from "@/hooks/use-api"
import { Users, Building2, TrendingUp, DollarSign } from "lucide-react"

const metricCards = [
  { key: "total_users", label: "Total Users", icon: Users },
  { key: "total_founders", label: "Founders", icon: Users },
  { key: "total_investors", label: "Investors", icon: DollarSign },
  { key: "total_startups", label: "Startups", icon: Building2 },
  { key: "active_deals", label: "Active Deals", icon: TrendingUp },
  { key: "closed_deals", label: "Closed Deals", icon: TrendingUp },
  { key: "active_subscriptions", label: "Active Subscriptions", icon: DollarSign },
  { key: "new_matches_30d", label: "New Matches (30 days)", icon: TrendingUp },
] as const

export default function AdminDashboardPage() {
  const { data, isLoading: isOverviewLoading } = useAdminDashboard()
  const { data: users, isLoading: isUsersLoading } = useAdminUsers()
  const { data: tickets, isLoading: isTicketsLoading } = useAdminTickets()

  const isLoading = isOverviewLoading || isUsersLoading || isTicketsLoading
  const recentUsers = (users || []).slice(0, 5)
  const openTickets = (tickets || []).filter((t: any) => t.status === "open").slice(0, 5)

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
              <span className="text-2xl font-bold" data-testid={`metric-${key}`}>{data?.[key] ?? 0}</span>
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
            {recentUsers.length === 0 ? (
              <div className="text-sm text-muted-foreground py-8 text-center border-2 border-dashed rounded-md">
                No recent users
              </div>
            ) : (
              <div className="space-y-3">
                {recentUsers.map((u: any) => (
                  <div key={u.id} className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium">{u.first_name} {u.last_name}</p>
                      <p className="text-xs text-muted-foreground">{u.email}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={u.role === "investor" ? "warning" : "default"}>{u.role}</Badge>
                      <span className="text-xs text-muted-foreground">{u.date_joined ? new Date(u.date_joined).toLocaleDateString() : ""}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Ticket Queue</CardTitle>
            <CardDescription>Open support tickets</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {openTickets.length === 0 ? (
              <div className="text-sm text-muted-foreground py-8 text-center border-2 border-dashed rounded-md">
                No open tickets
              </div>
            ) : (
              openTickets.map((t: any) => (
                <div key={t.id} className="flex flex-col gap-1 py-1 border-b last:border-0">
                  <p className="text-sm truncate">{t.subject}</p>
                  <div className="flex gap-1">
                    <Badge variant={t.priority === "high" || t.priority === "critical" ? "destructive" : t.priority === "medium" ? "warning" : "default"} className="text-[10px]">
                      {t.priority}
                    </Badge>
                    <Badge variant={t.status === "open" ? "default" : "secondary"} className="text-[10px]">
                      {t.status.replace("_", " ")}
                    </Badge>
                  </div>
                </div>
              ))
            )}
            <div className="flex items-center justify-between pt-2 text-sm border-t mt-2">
              <span className="text-muted-foreground">{data?.open_tickets ?? 0} open tickets</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
