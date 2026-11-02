"use client"

import { useRef, useState } from "react"
import { toast } from "sonner"
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { formatCurrency } from "@/lib/utils"
import { humanize } from "@/lib/constants"
import { useBillingAction, useInvoices, usePlans, useSubscribe, useSubscription } from "@/hooks/use-api"
import { AlertCircle, Check, CreditCard, Download, Receipt, X } from "lucide-react"
import type { Invoice, SubscriptionPlan } from "@/types/api"

function dateOrDash(value: string | null) {
  return value ? new Date(value).toLocaleDateString() : "-"
}

/** There is no invoice file endpoint, so this writes a plain text receipt from the invoice data. */
function downloadInvoice(inv: Invoice) {
  const text = [
    "DEMO INVOICE - NO REAL PAYMENT WAS TAKEN",
    "",
    `Invoice:  ${inv.invoice_number}`,
    `Plan:     ${inv.plan_name} (${inv.billing_cycle})`,
    `Amount:   ${formatCurrency(inv.amount, inv.currency || "USD")}`,
    `Status:   ${inv.status}`,
    `Period:   ${dateOrDash(inv.period_start)} to ${dateOrDash(inv.period_end)}`,
    `Issued:   ${dateOrDash(inv.created_at)}`,
  ].join("\n")
  const url = URL.createObjectURL(new Blob([text], { type: "text/plain" }))
  const a = document.createElement("a")
  a.href = url
  a.download = `${inv.invoice_number}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

function FeatureRows({ plan }: { plan: SubscriptionPlan }) {
  return (
    <>
      {Object.entries(plan.features ?? {}).map(([key, value]) => (
        <div key={key} className="flex items-center gap-2 text-sm">
          {value ? <Check className="h-4 w-4 shrink-0 text-emerald-500" /> : <X className="h-4 w-4 shrink-0 text-muted-foreground" />}
          <span className="capitalize">{humanize(key)}{typeof value === "number" ? `: ${value}` : ""}</span>
        </div>
      ))}
      {Object.entries(plan.limits ?? {}).map(([key, value]) => (
        <div key={key} className="flex items-center justify-between text-sm">
          <span className="capitalize text-muted-foreground">{humanize(key)}</span>
          <span>{value}</span>
        </div>
      ))}
    </>
  )
}

export default function BillingPage() {
  const { data: plans, isLoading: plansLoading } = usePlans()
  const { data: subscription, isLoading: subLoading } = useSubscription()
  const { data: invoices, isLoading: invLoading } = useInvoices()
  const subscribe = useSubscribe()
  const billingAction = useBillingAction()
  const [selectedCycle, setSelectedCycle] = useState<"monthly" | "yearly">("monthly")
  const plansRef = useRef<HTMLDivElement>(null)

  const currentPlanSlug = subscription?.status === "active" ? subscription.plan.slug : undefined

  if (plansLoading || subLoading) {
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

      <div role="note" className="flex items-center gap-2 rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm font-medium text-amber-400">
        <AlertCircle className="h-4 w-4 shrink-0" />
        Demo checkout: no real payment. No card is requested and nothing is charged.
      </div>

      {subscription && (
        <Card data-testid="current-plan">
          <CardHeader>
            <div className="flex items-center justify-between gap-2">
              <div>
                <CardTitle>Current Plan</CardTitle>
                <CardDescription>You are on the {subscription.plan.name} plan</CardDescription>
              </div>
              <Badge variant={subscription.status === "active" ? "success" : "warning"}>{subscription.status}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div><p className="text-sm text-muted-foreground">Billing Cycle</p><p className="font-medium capitalize">{subscription.billing_cycle}</p></div>
              <div><p className="text-sm text-muted-foreground">Start Date</p><p className="font-medium">{dateOrDash(subscription.start_date)}</p></div>
              <div><p className="text-sm text-muted-foreground">End Date</p><p className="font-medium">{dateOrDash(subscription.end_date)}</p></div>
              <div><p className="text-sm text-muted-foreground">Auto Renew</p><p className="font-medium">{subscription.auto_renew ? "Yes" : "No"}</p></div>
            </div>
            <div className="space-y-2"><FeatureRows plan={subscription.plan} /></div>
          </CardContent>
          <CardFooter className="flex-wrap gap-2">
            {subscription.status === "active" ? (
              <Button variant="outline" disabled={billingAction.isPending}
                onClick={() => {
                  if (confirm("Cancel your demo subscription?")) {
                    billingAction.mutate("cancel", { onSuccess: () => toast.success("Subscription cancelled") })
                  }
                }}>
                Cancel Subscription
              </Button>
            ) : (
              <Button variant="outline" disabled={billingAction.isPending}
                onClick={() => billingAction.mutate("renew", { onSuccess: () => toast.success("Subscription renewed") })}>
                Renew Subscription
              </Button>
            )}
            <Button onClick={() => plansRef.current?.scrollIntoView({ behavior: "smooth" })}>Change Plan</Button>
          </CardFooter>
        </Card>
      )}

      <div className="space-y-4" ref={plansRef}>
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Plans</h2>
          <div className="flex gap-1 rounded-lg border p-1">
            <Button variant={selectedCycle === "monthly" ? "default" : "ghost"} size="sm" onClick={() => setSelectedCycle("monthly")}>Monthly</Button>
            <Button variant={selectedCycle === "yearly" ? "default" : "ghost"} size="sm" onClick={() => setSelectedCycle("yearly")}>Yearly</Button>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {plans?.map((plan) => {
            const price = selectedCycle === "monthly" ? plan.monthly_price : plan.yearly_price
            const isCurrent = plan.slug === currentPlanSlug
            const isFree = plan.tier === "free"
            return (
              <Card key={plan.id} className={plan.is_popular ? "border-primary" : ""} data-testid={`plan-${plan.slug}`}>
                <CardHeader>
                  <div className="flex items-center justify-between gap-2">
                    <CardTitle>{plan.name}</CardTitle>
                    {plan.is_popular && <Badge>Popular</Badge>}
                  </div>
                  <CardDescription>
                    <span className="text-3xl font-bold text-foreground">{formatCurrency(price)}</span>
                    <span className="text-muted-foreground">/{selectedCycle === "monthly" ? "mo" : "yr"}</span>
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2"><FeatureRows plan={plan} /></CardContent>
                <CardFooter>
                  <Button
                    className="w-full"
                    variant={isCurrent ? "outline" : plan.is_popular ? "default" : "secondary"}
                    disabled={isCurrent || isFree || subscribe.isPending}
                    onClick={() => subscribe.mutate(
                      { plan_slug: plan.slug, billing_cycle: selectedCycle },
                      { onSuccess: () => toast.success(`Now on ${plan.name} (demo: no payment taken)`) },
                    )}
                  >
                    {isCurrent ? "Current Plan" : isFree ? "Default plan" : "Subscribe (demo)"}
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
                <div key={inv.id} className="flex flex-wrap items-center justify-between gap-2 p-4">
                  <div className="flex items-center gap-3">
                    <Receipt className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium">{inv.invoice_number}</p>
                      <p className="text-xs text-muted-foreground">{inv.plan_name} &middot; {new Date(inv.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium">{formatCurrency(inv.amount, inv.currency || "USD")}</span>
                    <Badge variant={inv.status === "paid" ? "success" : inv.status === "pending" ? "warning" : "destructive"}>{inv.status}</Badge>
                    <Button variant="ghost" size="icon" aria-label={`Download invoice ${inv.invoice_number}`} onClick={() => downloadInvoice(inv)}>
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
