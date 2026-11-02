"use client"

import { Suspense, useState } from "react"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { Brain } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { InsightPanel } from "@/components/insights/insight-panel"
import { useMatches } from "@/hooks/use-api"

function Content({ side }: { side: "investor" | "founder" }) {
  const preselected = Number(useSearchParams().get("match")) || null
  const [selectedId, setSelectedId] = useState<number | null>(preselected)
  const { data: matches, isLoading } = useMatches(side === "investor" ? "startup" : "investor")

  const sorted = [...(matches ?? [])].sort((a, b) => b.score - a.score)
  const active = sorted.find((m) => m.id === selectedId) ?? sorted[0]

  if (isLoading) {
    return (
      <div className="grid gap-6 lg:grid-cols-3">
        <Skeleton className="h-64" />
        <Skeleton className="h-64 lg:col-span-2" />
      </div>
    )
  }

  if (!active) {
    return (
      <Card>
        <CardContent className="p-12 text-center text-muted-foreground">
          <Brain className="mx-auto mb-2 h-8 w-8" />
          <p>No matches to analyze yet.</p>
          <Button asChild className="mt-4">
            {side === "investor"
              ? <Link href="/investor/discover">Discover startups</Link>
              : <Link href="/founder/startups">Publish a startup</Link>}
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <Card className="self-start">
        <CardHeader>
          <CardTitle className="text-sm font-medium">Select match</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {sorted.map((m) => (
            <button
              key={m.id}
              type="button"
              aria-pressed={active.id === m.id}
              onClick={() => setSelectedId(m.id)}
              className={`flex w-full items-center gap-3 rounded-lg border p-3 text-left text-sm transition-colors hover:bg-accent/30 ${active.id === m.id ? "border-primary bg-accent/20" : ""}`}
            >
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium">{side === "investor" ? m.startup_name : m.investor_name}</p>
                <p className="truncate text-xs text-muted-foreground">{side === "investor" ? m.startup_tagline : m.startup_name}</p>
              </div>
              <Badge variant={m.score >= 80 ? "success" : "warning"} className="shrink-0">{Math.round(m.score)}%</Badge>
            </button>
          ))}
        </CardContent>
      </Card>
      <div className="lg:col-span-2">
        <InsightPanel key={active.id} matchId={active.id} score={active.score} />
      </div>
    </div>
  )
}

export function InsightsView({ side }: { side: "investor" | "founder" }) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">AI Match Insights</h1>
        <p className="text-muted-foreground">Why a match scored the way it did, generated from the real match data</p>
      </div>
      <Suspense fallback={<Skeleton className="h-64" />}>
        <Content side={side} />
      </Suspense>
    </div>
  )
}
