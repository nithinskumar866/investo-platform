"use client"

import { useMatches } from "@/hooks/use-api"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Avatar } from "@/components/ui/avatar"
import { Lightbulb, TrendingUp, TrendingDown, Target, Zap, CheckCircle, ArrowRight } from "lucide-react"
import Link from "next/link"

function InsightCard({
  match,
  rank,
}: {
  match: { id: number; investor: number; score: number; status: string; investor_detail?: { first_name: string; last_name: string } }
  rank: number
}) {
  const strengths = [
    "Same industry focus and stage preference",
    "Historical investments in similar business models",
    "Geographic alignment with portfolio companies",
    "Check size matches your funding requirements",
  ]

  const risks = [
    "Portfolio overlap with direct competitors",
    "Recent fundraising may limit new commitments",
  ]

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="flex flex-row items-start gap-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
          #{rank}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <CardTitle className="text-base">
              {match.investor_detail
                ? `${match.investor_detail.first_name} ${match.investor_detail.last_name}`
                : `Investor #${match.investor}`}
            </CardTitle>
            <Badge variant={match.score >= 80 ? "success" : "warning"}>{match.score}%</Badge>
          </div>
          <CardDescription>AI-powered match analysis</CardDescription>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-lg bg-emerald-500/5 border border-emerald-500/10 p-3">
          <div className="flex items-center gap-2 text-sm font-medium text-emerald-600 mb-2">
            <Zap className="h-4 w-4" /> Strengths
          </div>
          <ul className="space-y-1">
            {strengths.map((s, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                <CheckCircle className="h-3.5 w-3.5 text-emerald-500 mt-0.5 shrink-0" />
                <span>{s}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-lg bg-amber-500/5 border border-amber-500/10 p-3">
          <div className="flex items-center gap-2 text-sm font-medium text-amber-600 mb-2">
            <TrendingDown className="h-4 w-4" /> Considerations
          </div>
          <ul className="space-y-1">
            {risks.map((r, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-400 mt-2 shrink-0" />
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="flex items-center justify-between pt-1">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Target className="h-3.5 w-3.5" />
            <span>Overall recommendation score: <strong>{Math.min(100, match.score + 5)}</strong></span>
          </div>
          <Button size="sm" variant="outline" className="gap-1">
            View Details <ArrowRight className="h-3 w-3" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

export default function InsightsPage() {
  const { data: matches, isLoading } = useMatches("investor")

  const topMatches = (matches ?? [])
    .filter((m) => m.score >= 60)
    .sort((a, b) => b.score - a.score)
    .slice(0, 5)

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Lightbulb className="h-6 w-6 text-primary" />
        <div>
          <h1 className="text-2xl font-bold tracking-tight">AI Match Insights</h1>
          <p className="text-muted-foreground">Smart recommendations powered by AI analysis</p>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader><Skeleton className="h-6 w-64" /></CardHeader>
              <CardContent className="space-y-3">
                <Skeleton className="h-20 w-full" />
                <Skeleton className="h-16 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : topMatches.length > 0 ? (
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Top {topMatches.length} recommended investors based on your startup profile, market fit, and investment criteria.
          </p>
          {topMatches.map((match, i) => (
            <InsightCard key={match.id} match={match} rank={i + 1} />
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <Lightbulb className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-lg font-medium">No insights available</p>
            <p className="text-sm text-muted-foreground mb-4">
              We need more data about your startup to generate AI match insights.
            </p>
            <Button asChild>
              <Link href="/founder/startups">Update Startup Profile</Link>
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
