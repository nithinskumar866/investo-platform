"use client"

import { useState } from "react"
import {
  Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { formatCurrency } from "@/lib/utils"
import { usePlans, useSubscription, useInvoices, useSubscribe } from "@/hooks/use-api"
import { Check, X, CreditCard, Download, Receipt } from "lucide-react"
import type { SubscriptionPlan } from "@/types/api"

const tierColors: Record<string, string> = {
  free: "default",
  founder_premium: "success",
  investor_premium: "warning",
  enterprise: "default",
}

const planDisplayNames: Record<string, string> = {
  free: "Free",
  founder_premium: "Founder Premium",
  investor_premium: "Investor Premium",
  enterprise: "Enterprise",
}

export default function BillingPage() {
  const { data: plans, isLoading: plansLoading } = usePlans()
  const { data: subscription, isLoading: subLoading } = useSubscription()
  const { data: invoices, isLoading: invLoading } = useInvoices()
  const subscribe = useSubscribe()
  const [selectedCycle, setSelectedCycle] = useState<"monthly" | "yearly">("monthly")

  const currentPlanSlug = subscription?.plan?.slug
  const isLoading = plansLoading || subLoading

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Billing</h1>
        <p className="text-muted-foreground">Manage your subscription and view invoices</p>
      </div>

      {subscription && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Current Plan</CardTitle>
                <CardDescription>You are on the {planDisplayNames[currentPlanSlug || "free"]} plan</CardDescription>
              </div>
              <Badge variant={subscription.status === "active" ? "success" : "warning"}>
                {subscription.status}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div>
                <p className="text-sm text-muted-foreground">Billing Cycle</p>
                <p className="font-medium capitalize">{subscription.billing_cycle}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Start Date</p>
                <p className="font-medium">{new Date(subscription.start_date).toLocaleDateString()}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">End Date</p>
                <p className="font-medium">{new Date(subscription.end_date).toLocaleDateString()}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Auto Renew</p>
                <p className="font-medium">{subscription.auto_renew ? "Yes" : "No"}</p>
              </div>
            </div>
            <div className="space-y-2">
              {subscription.plan.features &&
                Object.entries(subscription.plan.features).map(([key, value]) => (
                  <div key={key} className="flex items-center gap-2 text-sm">
                    {value ? <Check className="h-4 w-4 text-emerald-500" /> : <X className="h-4 w-4 text-muted-foreground" />}
                    <span className="capitalize">{key.replace(/_/g, " ")}</span>
                  </div>
                ))}
            </div>
          </CardContent>
          <CardFooter className="gap-2">
            <Button variant="outline">Cancel Subscription</Button>
            <Button>Change Plan</Button>
          </CardFooter>
        </Card>
      )}

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Plans</h2>
          <div className="flex gap-1 rounded-lg border p-1">
            <Button
              variant={selectedCycle === "monthly" ? "default" : "ghost"}
              size="sm"
              onClick={() => setSelectedCycle("monthly")}
            >
              Monthly
            </Button>
            <Button
              variant={selectedCycle === "yearly" ? "default" : "ghost"}
              size="sm"
              onClick={() => setSelectedCycle("yearly")}
            >
              Yearly
            </Button>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {plans?.map((plan: SubscriptionPlan) => {
            const price = selectedCycle === "monthly" ? plan.monthly_price : plan.yearly_price
            const isCurrent = plan.slug === currentPlanSlug
            return (
              <Card key={plan.id} className={plan.is_popular ? "border-primary" : ""}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>{planDisplayNames[plan.slug]}</CardTitle>
                    {plan.is_popular && <Badge>Popular</Badge>}
                  </div>
                  <CardDescription>
                    <span className="text-3xl font-bold text-foreground">{formatCurrency(price)}</span>
                    <span className="text-muted-foreground">/{selectedCycle === "monthly" ? "mo" : "yr"}</span>
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  {plan.features &&
                    Object.entries(plan.features).map(([key, value]) => (
                      <div key={key} className="flex items-center gap-2 text-sm">
                        {value ? (
                          <Check className="h-4 w-4 text-emerald-500" />
                        ) : (
                          <X className="h-4 w-4 text-muted-foreground" />
                        )}
                        <span className="capitalize">{key.replace(/_/g, " ")}</span>
                      </div>
                    ))}
                  {plan.limits &&
                    Object.entries(plan.limits).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between text-sm">
                        <span className="capitalize text-muted-foreground">{key.replace(/_/g, " ")}</span>
                        <span>{value}</span>
                      </div>
                    ))}
                </CardContent>
                <CardFooter>
                  <Button
                    className="w-full"
                    variant={isCurrent ? "outline" : plan.is_popular ? "default" : "secondary"}
                    disabled={isCurrent || subscribe.isPending}
                    onClick={() => subscribe.mutate({ plan_slug: plan.slug, billing_cycle: selectedCycle })}
                  >
                    {isCurrent ? "Current Plan" : "Subscribe"}
                  </Button>
                </CardFooter>
              </Card>
            )
          })}
        </div>
      </div>

      <div className="space-y-4">
        <h2 className="text-xl font-semibold">Invoices</h2>
        {invLoading ? (
          <div className="space-y-2">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        ) : invoices && invoices.length > 0 ? (
          <Card>
            <div className="divide-y">
              {invoices.map((inv) => (
                <div key={inv.id} className="flex items-center justify-between p-4">
                  <div className="flex items-center gap-3">
                    <Receipt className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium">{inv.invoice_number}</p>
                      <p className="text-xs text-muted-foreground">{inv.plan_name} &middot; {new Date(inv.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium">{formatCurrency(inv.amount)}</span>
                    <Badge variant={inv.status === "paid" ? "success" : inv.status === "pending" ? "warning" : "destructive"}>
                      {inv.status}
                    </Badge>
                    <Button variant="ghost" size="icon">
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        ) : (
          <Card>
            <CardContent className="flex flex-col items-center gap-2 py-12 text-center">
              <CreditCard className="h-8 w-8 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">No invoices yet</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
