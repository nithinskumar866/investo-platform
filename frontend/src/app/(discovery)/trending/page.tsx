"use client"

import { useStartups, useInvestments } from "@/hooks/use-api"
import { formatCurrency, formatRelativeTime } from "@/lib/utils"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { TrendingUp, Building2, Users, Briefcase, ArrowUpRight } from "lucide-react"

function TrendingSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-6 w-40" />
      {Array.from({ length: 3 }).map((_, i) => (
        <Card key={i}>
          <CardContent className="p-4">
            <Skeleton className="mb-2 h-5 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

export default function TrendingPage() {
  const { data: startups, isLoading: startupsLoading } = useStartups()
  const { data: investments, isLoading: investmentsLoading } = useInvestments()

  if (startupsLoading || investmentsLoading) {
    return (
      <div className="grid gap-6 lg:grid-cols-3">
        <TrendingSkeleton />
        <TrendingSkeleton />
        <TrendingSkeleton />
      </div>
    )
  }

  const topStartups = startups?.slice(0, 5) || []
  const topInvestors = investments?.slice(0, 5) || []
  const topOpportunities = investments?.filter((i) => i.status === "pending").slice(0, 5) || []

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-primary" />
            Trending Now
          </CardTitle>
        </CardHeader>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        <section>
          <div className="mb-3 flex items-center gap-2">
            <Building2 className="h-4 w-4 text-primary" />
            <h2 className="font-semibold">Popular Startups</h2>
          </div>
          <div className="space-y-3">
            {topStartups.map((s, i) => (
              <Card key={s.id} className="transition-colors hover:bg-accent/50">
                <CardContent className="flex items-center gap-3 p-4">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
                    {i + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium truncate">{s.name}</p>
                      <Badge variant="secondary" className="text-xs">{s.stage}</Badge>
                    </div>
                    <p className="text-xs text-muted-foreground truncate">{s.tagline}</p>
                  </div>
                  <ArrowUpRight className="h-4 w-4 shrink-0 text-muted-foreground" />
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        <section>
          <div className="mb-3 flex items-center gap-2">
            <Users className="h-4 w-4 text-primary" />
            <h2 className="font-semibold">Active Investors</h2>
          </div>
          <div className="space-y-3">
            {topInvestors.map((inv, i) => (
              <Card key={inv.id} className="transition-colors hover:bg-accent/50">
                <CardContent className="flex items-center gap-3 p-4">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
                    {i + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">{inv.startup_name || `Investor ${inv.investor}`}</p>
                    <p className="text-xs text-muted-foreground">
                      {inv.amount_offered ? formatCurrency(inv.amount_offered) : "Undisclosed"} offered
                    </p>
                  </div>
                  <Badge variant={inv.status === "accepted" ? "success" : "warning"} className="text-xs">
                    {inv.status}
                  </Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        <section>
          <div className="mb-3 flex items-center gap-2">
            <Briefcase className="h-4 w-4 text-primary" />
            <h2 className="font-semibold">Top Opportunities</h2>
          </div>
          <div className="space-y-3">
            {topOpportunities.map((opp, i) => (
              <Card key={opp.id} className="transition-colors hover:bg-accent/50">
                <CardContent className="flex items-center gap-3 p-4">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
                    {i + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">{opp.startup_name || `Opportunity #${opp.id}`}</p>
                    <p className="text-xs text-muted-foreground">
                      {opp.amount_requested ? formatCurrency(opp.amount_requested) : "Undisclosed"} requested
                    </p>
                  </div>
                  <span className="text-xs text-muted-foreground shrink-0">{formatRelativeTime(opp.created_at)}</span>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
