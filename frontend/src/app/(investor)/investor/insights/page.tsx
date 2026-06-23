"use client"

import { useState } from "react"
import { useMatches, useMatchInsight } from "@/hooks/use-api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Avatar } from "@/components/ui/avatar"
import { Lightbulb, Brain, ThumbsUp, AlertTriangle, ArrowRight, Target } from "lucide-react"
import Link from "next/link"

export default function InsightsPage() {
  const [selectedMatchId, setSelectedMatchId] = useState<number | null>(null)
  const { data: matches, isLoading: mLoading } = useMatches("startup")
  const { data: insight, isLoading: iLoading } = useMatchInsight(selectedMatchId ?? 0)

  const sorted = [...(matches ?? [])].sort((a, b) => b.score - a.score)
  const selectedMatch = sorted.find((m) => m.id === selectedMatchId) ?? sorted[0]
  const activeId = selectedMatch?.id

  if (mLoading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64 mt-2" />
        </div>
        <div className="grid gap-6 lg:grid-cols-3">
          <Skeleton className="h-64" />
          <Skeleton className="h-64 lg:col-span-2" />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">AI Match Insights</h1>
        <p className="text-muted-foreground">Deep-dive analysis powered by AI matching engine</p>
      </div>

      {sorted.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center text-muted-foreground">
            <Brain className="mx-auto mb-2 h-8 w-8" />
            <p>No matches to analyze yet.</p>
            <p className="text-sm">Discover startups to generate AI insights.</p>
            <Button asChild className="mt-4">
              <Link href="/investor/discover">Discover Startups</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Select Match</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {sorted.map((m) => {
                const s = m.startup_detail
                return (
                  <button
                    key={m.id}
                    onClick={() => setSelectedMatchId(m.id)}
                    className={`w-full flex items-center gap-3 rounded-lg border p-3 text-left text-sm transition-colors hover:bg-accent ${
                      activeId === m.id ? "border-primary bg-accent" : ""
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{s?.name ?? `Startup #${m.startup}`}</p>
                      <p className="text-xs text-muted-foreground truncate">{s?.tagline}</p>
                    </div>
                    <Badge variant={m.score >= 80 ? "success" : "warning"} className="shrink-0">
                      {Math.round(m.score)}%
                    </Badge>
                  </button>
                )
              })}
            </CardContent>
          </Card>

          <div className="lg:col-span-2 space-y-4">
            {!activeId ? (
              <Card>
                <CardContent className="p-12 text-center text-muted-foreground">
                  Select a match to view insights
                </CardContent>
              </Card>
            ) : iLoading ? (
              <Card>
                <CardContent className="p-6 space-y-4">
                  <Skeleton className="h-6 w-3/4" />
                  <Skeleton className="h-20 w-full" />
                  <Skeleton className="h-20 w-full" />
                </CardContent>
              </Card>
            ) : insight ? (
              <>
                <Card>
                  <CardHeader className="flex flex-row items-center gap-2">
                    <Brain className="h-5 w-5 text-primary" />
                    <CardTitle>AI Summary</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-sm text-muted-foreground">Overall Score</span>
                      <Badge
                        variant={insight.overall_score >= 80 ? "success" : insight.overall_score >= 50 ? "warning" : "secondary"}
                        className="text-sm"
                      >
                        {Math.round(insight.overall_score)}%
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{insight.summary}</p>
                  </CardContent>
                </Card>

                <div className="grid gap-4 sm:grid-cols-2">
                  <Card>
                    <CardHeader className="flex flex-row items-center gap-2">
                      <ThumbsUp className="h-4 w-4 text-emerald-500" />
                      <CardTitle className="text-sm">Strengths</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {insight.strengths.length === 0 ? (
                        <p className="text-sm text-muted-foreground">No specific strengths identified.</p>
                      ) : (
                        <ul className="space-y-2">
                          {insight.strengths.map((s, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm">
                              <ArrowRight className="mt-0.5 h-3 w-3 shrink-0 text-emerald-500" />
                              <span>{s}</span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-amber-500" />
                      <CardTitle className="text-sm">Risks</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {insight.risks.length === 0 ? (
                        <p className="text-sm text-muted-foreground">No significant risks identified.</p>
                      ) : (
                        <ul className="space-y-2">
                          {insight.risks.map((r, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm">
                              <ArrowRight className="mt-0.5 h-3 w-3 shrink-0 text-amber-500" />
                              <span>{r}</span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </CardContent>
                  </Card>
                </div>

                <Card>
                  <CardHeader className="flex flex-row items-center gap-2">
                    <Target className="h-4 w-4 text-primary" />
                    <CardTitle className="text-sm">Recommendations</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {insight.recommendations.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No recommendations available.</p>
                    ) : (
                      <ul className="space-y-2">
                        {insight.recommendations.map((r, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm">
                            <ArrowRight className="mt-0.5 h-3 w-3 shrink-0 text-primary" />
                            <span>{r}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card>
                <CardContent className="p-12 text-center text-muted-foreground">
                  No insight data available for this match.
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
