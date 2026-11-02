"use client"

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Progress } from "@/components/ui/progress"
import { useAdminRevenue } from "@/hooks/use-api"
import { formatCurrency } from "@/lib/utils"

export default function AdminRevenuePage() {
  const { data, isLoading } = useAdminRevenue()

  if (isLoading || !data) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-24" />)}
        </div>
      </div>
    )
  }

  const cards: [string, string | number][] = [
    ["MRR", formatCurrency(data.mrr)],
    ["ARR", formatCurrency(data.arr)],
    ["Last month", formatCurrency(data.last_month_revenue)],
    ["Total revenue", formatCurrency(data.total_revenue)],
    ["Active subscriptions", data.active_subscriptions],
    ["Churned this month", data.churned_this_month],
    ["Active trials", data.trial_active],
    ["Trials converted", data.trial_converted],
  ]
  const totalPlans = data.plan_distribution.reduce((sum, p) => sum + p.count, 0)

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Revenue Analytics</h1>
        <p className="text-muted-foreground">From demo checkouts: no real payments are taken</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map(([label, value]) => (
          <Card key={label}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Plan distribution</CardTitle>
          <CardDescription>Active subscriptions by plan</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {data.plan_distribution.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">No active subscriptions.</p>
          ) : (
            data.plan_distribution.map((plan) => (
              <div key={plan.plan__name} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span>{plan.plan__name}</span>
                  <span className="text-muted-foreground">{plan.count} subscriber{plan.count === 1 ? "" : "s"}</span>
                </div>
                <Progress value={totalPlans ? (plan.count / totalPlans) * 100 : 0} className="h-2" aria-label={plan.plan__name} />
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  )
}
