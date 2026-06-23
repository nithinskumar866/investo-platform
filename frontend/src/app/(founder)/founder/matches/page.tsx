"use client"

import { useState } from "react"
import { useMatches } from "@/hooks/use-api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Avatar } from "@/components/ui/avatar"
import { MessageSquare, Calendar, ArrowUpDown, Star } from "lucide-react"

export default function MatchesPage() {
  const { data: matches, isLoading } = useMatches("investor")
  const [sortBy, setSortBy] = useState<"score" | "date">("score")

  const sorted = [...(matches ?? [])].sort((a, b) =>
    sortBy === "score" ? b.score - a.score : new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Matched Investors</h1>
          <p className="text-muted-foreground">Investors matched to your startup profile</p>
        </div>
        <Button variant="outline" size="sm" className="gap-2" onClick={() => setSortBy((s) => (s === "score" ? "date" : "score"))}>
          <ArrowUpDown className="h-4 w-4" />
          Sort by {sortBy === "score" ? "Date" : "Score"}
        </Button>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardHeader><Skeleton className="h-5 w-48" /></CardHeader>
              <CardContent className="space-y-3">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-8 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {sorted.map((match) => (
            <Card key={match.id}>
              <CardHeader className="flex flex-row items-start gap-4">
                <Avatar
                  fallback={match.investor_detail?.first_name?.[0] ?? "I"}
                  className="h-10 w-10"
                />
                <div className="flex-1 min-w-0">
                  <CardTitle className="text-base">
                    {match.investor_detail
                      ? `${match.investor_detail.first_name} ${match.investor_detail.last_name}`
                      : `Investor #${match.investor}`}
                  </CardTitle>
                  <p className="text-xs text-muted-foreground">
                    Matched {new Date(match.created_at).toLocaleDateString()}
                  </p>
                </div>
                <Badge
                  variant={match.score >= 80 ? "success" : match.score >= 50 ? "warning" : "secondary"}
                  className="shrink-0 text-sm px-3 py-1"
                >
                  {match.score}%
                </Badge>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-3">
                  {match.score >= 80
                    ? "Strong alignment with your sector, stage, and funding needs."
                    : match.score >= 50
                    ? "Moderate alignment. Consider reaching out to discuss further."
                    : "Limited alignment based on current profile data."}
                </p>
                <div className="flex items-center gap-2 mb-3">
                  {match.status && <Badge variant="outline">{match.status}</Badge>}
                  {match.is_bookmarked && (
                    <Badge variant="secondary" className="gap-1">
                      <Star className="h-3 w-3" /> Saved
                    </Badge>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button size="sm" className="flex-1 gap-1">
                    <MessageSquare className="h-3.5 w-3.5" /> Message
                  </Button>
                  <Button size="sm" variant="outline" className="flex-1 gap-1">
                    <Calendar className="h-3.5 w-3.5" /> Request Meeting
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {!isLoading && !matches?.length && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <Star className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-lg font-medium">No matches yet</p>
            <p className="text-sm text-muted-foreground">Complete your startup profile to get matched with investors.</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
