"use client"

import { useMemo } from "react"
import { useInvestments } from "@/hooks/use-api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { formatCurrency } from "@/lib/utils"
import { Building2, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"

const stages = ["Lead", "Intro", "Meeting", "Term Sheet", "Closed"]
const stageColors: Record<string, string> = {
  Lead: "border-t-blue-500",
  Intro: "border-t-violet-500",
  Meeting: "border-t-amber-500",
  "Term Sheet": "border-t-rose-500",
  Closed: "border-t-emerald-500",
}

function getStage(status: string): string {
  const map: Record<string, string> = {
    pending: "Lead",
    reviewing: "Intro",
    meeting: "Meeting",
    terms: "Term Sheet",
    closed: "Closed",
    won: "Closed",
    lost: "Closed",
  }
  return map[status.toLowerCase()] ?? "Lead"
}

export default function DealsPage() {
  const { data: investments, isLoading } = useInvestments()

  const columns = useMemo(() => {
    const cols: Record<string, NonNullable<typeof investments>> = { Lead: [], Intro: [], Meeting: [], "Term Sheet": [], Closed: [] }
    ;(investments ?? []).forEach((inv) => {
      const stage = getStage(inv.status)
      if (cols[stage]) cols[stage].push(inv)
      else cols["Lead"].push(inv)
    })
    return cols
  }, [investments])

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64 mt-2" />
        </div>
        <div className="flex gap-4 overflow-x-auto pb-4">
          {stages.map((s) => (
            <Card key={s} className="min-w-[280px] flex-1">
              <CardHeader><Skeleton className="h-5 w-24" /></CardHeader>
              <CardContent className="space-y-3">
                {Array.from({ length: 2 }).map((_, i) => (
                  <Skeleton key={i} className="h-24 w-full" />
                ))}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Deal Pipeline</h1>
          <p className="text-muted-foreground">{investments?.length ?? 0} active deals</p>
        </div>
        <Button>
          <Plus className="mr-1 h-4 w-4" /> Add Deal
        </Button>
      </div>

      <div className="flex gap-4 overflow-x-auto pb-4">
        {stages.map((stage) => {
          const deals = columns[stage] ?? []
          return (
            <div key={stage} className="min-w-[280px] flex-1">
              <Card className={`border-t-2 ${stageColors[stage] ?? ""}`}>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium">{stage}</CardTitle>
                    <Badge variant="secondary">{deals.length}</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3 min-h-[200px]">
                  {deals.length === 0 ? (
                    <div className="flex items-center justify-center h-20 rounded-lg border border-dashed text-xs text-muted-foreground">
                      Drop deal here
                    </div>
                  ) : (
                    deals.map((deal) => (
                      <Card key={deal.id} className="shadow-sm">
                        <CardContent className="p-3 space-y-2">
                          <div className="flex items-center gap-2">
                            <Building2 className="h-4 w-4 shrink-0 text-muted-foreground" />
                            <span className="text-sm font-medium truncate">
                              {deal.startup_name ?? `Startup #${deal.startup}`}
                            </span>
                          </div>
                          <div className="flex items-center justify-between text-xs text-muted-foreground">
                            <span>{deal.amount_offered ? formatCurrency(deal.amount_offered) : "—"}</span>
                            <Badge variant="outline" className="text-[10px]">{deal.status}</Badge>
                          </div>
                        </CardContent>
                      </Card>
                    ))
                  )}
                </CardContent>
              </Card>
            </div>
          )
        })}
      </div>
    </div>
  )
}
