"use client"

import { useEffect, useState } from "react"
import { AlertTriangle, ArrowRight, Brain, Loader2, RefreshCw, Target, ThumbsUp } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useMatchInsight, useRegenerateInsight } from "@/hooks/use-api"

function GeneratingCard() {
  const [seconds, setSeconds] = useState(0)
  useEffect(() => {
    const id = setInterval(() => setSeconds((s) => s + 1), 1000)
    return () => clearInterval(id)
  }, [])
  return (
    <Card>
      <CardContent className="flex flex-col items-center gap-3 p-12 text-center" role="status">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="font-medium">Generating the explanation...</p>
        <p className="text-sm text-muted-foreground">
          A local AI model runs on the CPU, so this can take up to about a minute. {seconds}s so far.
        </p>
      </CardContent>
    </Card>
  )
}

/** Shows the real /matching/insights/{id}/ result. Used by both founder and investor pages. */
export function InsightPanel({ matchId, score }: { matchId: number; score?: number }) {
  const { data: insight, isLoading, error, refetch, isFetching } = useMatchInsight(matchId)
  const regenerate = useRegenerateInsight(matchId)

  if (isLoading || regenerate.isPending || (isFetching && !insight)) return <GeneratingCard />

  if (error || !insight) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center gap-3 p-12 text-center text-muted-foreground">
          <p>This explanation could not be loaded. It may be an old saved one, so try generating a fresh one.</p>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => refetch()}>Try again</Button>
            <Button onClick={() => regenerate.mutate()}>Generate a fresh explanation</Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4" data-testid="insight">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-primary" />
            <CardTitle>Summary</CardTitle>
            {score !== undefined && (
              <Badge variant={score >= 80 ? "success" : score >= 50 ? "warning" : "secondary"}>{Math.round(score)}% match</Badge>
            )}
          </div>
          <Button variant="ghost" size="sm" onClick={() => regenerate.mutate()}>
            <RefreshCw className="mr-1 h-3 w-3" /> Regenerate
          </Button>
        </CardHeader>
        <CardContent>
          <p className="whitespace-pre-line text-sm text-muted-foreground">{insight.summary}</p>
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center gap-2 pb-3">
            <ThumbsUp className="h-4 w-4 text-emerald-500" />
            <CardTitle className="text-sm">Strengths</CardTitle>
          </CardHeader>
          <CardContent>
            {insight.strengths.length === 0 ? (
              <p className="text-sm text-muted-foreground">No specific strengths identified.</p>
            ) : (
              <ul className="space-y-3">
                {insight.strengths.map((s) => (
                  <li key={s.factor} className="text-sm">
                    <p className="font-medium">{s.label} <span className="text-xs font-normal text-muted-foreground">({Math.round(s.score)}/100)</span></p>
                    <p className="text-muted-foreground">{s.description}</p>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center gap-2 pb-3">
            <AlertTriangle className="h-4 w-4 text-amber-500" />
            <CardTitle className="text-sm">Risks</CardTitle>
          </CardHeader>
          <CardContent>
            {insight.risks.length === 0 ? (
              <p className="text-sm text-muted-foreground">No significant risks identified.</p>
            ) : (
              <ul className="space-y-3">
                {insight.risks.map((r) => (
                  <li key={r.factor} className="text-sm">
                    <p className="font-medium">{r.label} <span className="text-xs font-normal text-muted-foreground">({Math.round(r.score)}/100)</span></p>
                    <p className="text-muted-foreground">{r.description}</p>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center gap-2 pb-3">
          <Target className="h-4 w-4 text-primary" />
          <CardTitle className="text-sm">Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          {insight.recommendations.length === 0 ? (
            <p className="text-sm text-muted-foreground">No recommendations available.</p>
          ) : (
            <ul className="space-y-3">
              {insight.recommendations.map((r, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <ArrowRight className="mt-0.5 h-3 w-3 shrink-0 text-primary" />
                  <div>
                    <p className="font-medium">{r.action} <Badge variant="outline" className="ml-1 text-[10px] capitalize">{r.priority}</Badge></p>
                    <p className="text-muted-foreground">{r.detail}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
