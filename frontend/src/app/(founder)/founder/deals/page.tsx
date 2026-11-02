"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { DealBoard } from "@/components/deals/deal-board"
import { useFounderDeals, useMyStartups } from "@/hooks/use-api"

export default function DealsPage() {
  const { data: startups, isLoading: startupsLoading } = useMyStartups()
  const { data: deals, isLoading: dealsLoading } = useFounderDeals(startups?.map((s) => s.id))
  const isLoading = startupsLoading || dealsLoading

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Deal Pipeline</h1>
        <p className="text-muted-foreground">Investors interested in your startups. All amounts are dummy money.</p>
      </div>
      {!isLoading && startups?.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-12 text-center text-muted-foreground">
            <p>Deals appear here once you have a published startup.</p>
            <Button asChild><Link href="/founder/startups/new">Create a startup</Link></Button>
          </CardContent>
        </Card>
      ) : !isLoading && deals?.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No investor has expressed interest yet. Deals start when an investor does so on your startup page.
          </CardContent>
        </Card>
      ) : (
        <DealBoard deals={deals} side="startup" isLoading={isLoading} />
      )}
    </div>
  )
}
