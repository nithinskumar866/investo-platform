"use client"

import {
  Card, CardHeader, CardTitle, CardDescription, CardContent,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { useAdminRevenue } from "@/hooks/use-api"
import { formatCurrency } from "@/lib/utils"
import { TrendingUp, DollarSign, Users, Activity } from "lucide-react"

export default function AdminRevenuePage() {
  const { data, isLoading } = useAdminRevenue()

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <Skeleton className="h-72" />
          <Skeleton className="h-72" />
        </div>
        <Skeleton className="h-80" />
      </div>
    )
  }

  const metrics = data as Record<string, unknown> | undefined
  const mrr = (metrics?.mrr as number) ?? 0
  const activeSubscriptions = (metrics?.active_subscriptions as number) ?? 0
  const churnRate = (metrics?.churn_rate as number) ?? 0
  const avgRevenuePerUser = (metrics?.avg_revenue_per_user as number) ?? 0
  const planDistribution = (metrics?.plan_distribution as Array<{ name: string; count: number; revenue: number }>) ?? []
  const topCustomers = (metrics?.top_customers as Array<{ name: string; email: string; plan: string; mrr: number }>) ?? []

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Revenue Analytics</h1>
        <p className="text-muted-foreground">Financial metrics and subscription data</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">MRR</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(mrr)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Active Subscriptions</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeSubscriptions}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Churn Rate</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{churnRate}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Avg Revenue/User</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(avgRevenuePerUser)}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>MRR Trend</CardTitle>
            <CardDescription>Monthly recurring revenue over time</CardDescription>
          </CardHeader>
          <CardContent className="flex items-center justify-center h-60">
            <div className="text-center text-muted-foreground">
              <TrendingUp className="h-8 w-8 mx-auto mb-2" />
              <p className="text-sm">Chart placeholder</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Plan Distribution</CardTitle>
            <CardDescription>Revenue by plan tier</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {planDistribution.map((plan) => (
              <div key={plan.name} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span>{plan.name}</span>
                  <span className="font-medium">{formatCurrency(plan.revenue)}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-2 flex-1 rounded-full bg-primary/20">
                    <div
                      className="h-2 rounded-full bg-primary"
                      style={{ width: `${mrr > 0 ? (plan.revenue / mrr) * 100 : 0}%` }}
                    />
                  </div>
                  <span className="text-xs text-muted-foreground">{plan.count} users</span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Top Customers</CardTitle>
          <CardDescription>Highest MRR accounts</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="divide-y">
            {topCustomers.map((c, i) => (
              <div key={i} className="flex items-center justify-between py-3">
                <div>
                  <p className="text-sm font-medium">{c.name}</p>
                  <p className="text-xs text-muted-foreground">{c.email}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{c.plan}</Badge>
                  <span className="text-sm font-medium">{formatCurrency(c.mrr)}/mo</span>
                </div>
              </div>
            ))}
            {topCustomers.length === 0 && (
              <p className="py-8 text-center text-sm text-muted-foreground">No data available</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
