"use client"

import Link from "next/link"
import { Search } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { DealBoard } from "@/components/deals/deal-board"
import { useInvestorDeals } from "@/hooks/use-api"

export default function DealsPage() {
  const { data: deals, isLoading } = useInvestorDeals()
  const active = (deals ?? []).filter((d) => !["invested", "rejected", "withdrawn"].includes(d.status)).length

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Deal Pipeline</h1>
          <p className="text-muted-foreground">{active} active deal{active === 1 ? "" : "s"}. All amounts are dummy money.</p>
        </div>
        <Button asChild>
          <Link href="/investor/discover"><Search className="mr-1 h-4 w-4" /> Find startups</Link>
        </Button>
      </div>
      {!isLoading && deals?.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No deals yet. Open a startup and choose Express interest to start one.
          </CardContent>
        </Card>
      ) : (
        <DealBoard deals={deals} side="investor" isLoading={isLoading} />
      )}
    </div>
  )
}
