"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Avatar } from "@/components/ui/avatar"
import { Briefcase, Plus, ArrowRight, DollarSign, Calendar } from "lucide-react"
import { formatCurrency, formatDate } from "@/lib/utils"

type Deal = {
  id: number
  investorName: string
  investorInitials: string
  amount: number
  stage: string
  date: string
  notes: string
}

const stages = ["Lead", "Intro", "Meeting", "Term Sheet", "Closed"]

const dealsByStage: Record<string, Deal[]> = {
  Lead: [
    { id: 1, investorName: "Sarah Chen", investorInitials: "SC", amount: 500000, stage: "Lead", date: "2026-06-15", notes: "Initial contact made via email" },
    { id: 2, investorName: "Marcus Johnson", investorInitials: "MJ", amount: 1000000, stage: "Lead", date: "2026-06-14", notes: "Warm intro from mentor" },
  ],
  Intro: [
    { id: 3, investorName: "Priya Patel", investorInitials: "PP", amount: 750000, stage: "Intro", date: "2026-06-10", notes: "Intro call scheduled" },
  ],
  Meeting: [
    { id: 4, investorName: "Alex Rivera", investorInitials: "AR", amount: 2000000, stage: "Meeting", date: "2026-06-05", notes: "First meeting completed, follow-up requested" },
    { id: 5, investorName: "Emily Watson", investorInitials: "EW", amount: 300000, stage: "Meeting", date: "2026-06-01", notes: "Due diligence in progress" },
  ],
  "Term Sheet": [
    { id: 6, investorName: "David Kim", investorInitials: "DK", amount: 1500000, stage: "Term Sheet", date: "2026-05-20", notes: "Term sheet received, under review" },
  ],
  Closed: [
    { id: 7, investorName: "Lisa Thompson", investorInitials: "LT", amount: 500000, stage: "Closed", date: "2026-04-10", notes: "Deal closed successfully" },
  ],
}

function DealCard({ deal }: { deal: Deal }) {
  return (
    <Card className="mb-3 cursor-grab active:cursor-grabbing">
      <CardContent className="p-3 space-y-2">
        <div className="flex items-center gap-2">
          <Avatar fallback={deal.investorInitials} className="h-6 w-6 text-xs" />
          <span className="text-sm font-medium">{deal.investorName}</span>
        </div>
        <div className="flex items-center gap-1 text-sm font-semibold">
          <DollarSign className="h-3.5 w-3.5 text-muted-foreground" />
          {formatCurrency(deal.amount)}
        </div>
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Calendar className="h-3 w-3" />
          {formatDate(deal.date)}
        </div>
        <p className="text-xs text-muted-foreground line-clamp-2">{deal.notes}</p>
      </CardContent>
    </Card>
  )
}

export default function DealsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Deal Pipeline</h1>
          <p className="text-muted-foreground">Track your fundraising deal flow</p>
        </div>
        <Button className="gap-2">
          <Plus className="h-4 w-4" /> Add Deal
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {stages.map((stage) => {
          const deals = dealsByStage[stage] ?? []
          return (
            <div key={stage} className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold">{stage}</h3>
                  <Badge variant="secondary" className="h-5 px-1.5 text-xs">
                    {deals.length}
                  </Badge>
                </div>
                <Button variant="ghost" size="icon" className="h-6 w-6">
                  <Plus className="h-3 w-3" />
                </Button>
              </div>
              <div className="rounded-lg border border-border bg-muted/30 p-2 min-h-[200px]">
                {deals.map((deal) => (
                  <DealCard key={deal.id} deal={deal} />
                ))}
                {deals.length === 0 && (
                  <div className="flex h-32 items-center justify-center">
                    <p className="text-xs text-muted-foreground">No deals</p>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
