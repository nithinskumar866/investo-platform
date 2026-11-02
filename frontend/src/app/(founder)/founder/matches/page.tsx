"use client"

import { useState } from "react"
import Link from "next/link"
import { useMatches } from "@/hooks/use-api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Avatar } from "@/components/ui/avatar"
import { MeetingDialog } from "@/components/meetings/meeting-dialog"
import { MessageSquare, Calendar, ArrowUpDown, Sparkles, Star } from "lucide-react"
import { humanize } from "@/lib/constants"
import { getInitials } from "@/lib/utils"
import type { MatchScore } from "@/types/api"

export default function MatchesPage() {
  const { data: matches, isLoading } = useMatches("investor")
  const [sortBy, setSortBy] = useState<"score" | "date">("score")
  const [meetingMatch, setMeetingMatch] = useState<MatchScore | null>(null)

  const sorted = [...(matches ?? [])].sort((a, b) =>
    sortBy === "score" ? b.score - a.score : new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Matched Investors</h1>
          <p className="text-muted-foreground">Investors matched to your startups</p>
        </div>
        <Button variant="outline" size="sm" className="gap-2" onClick={() => setSortBy((s) => (s === "score" ? "date" : "score"))}>
          <ArrowUpDown className="h-4 w-4" />
          Sort by {sortBy === "score" ? "Date" : "Score"}
        </Button>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-48" />)}
        </div>
      ) : sorted.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <Star className="mb-4 h-12 w-12 text-muted-foreground" />
            <p className="text-lg font-medium">No matches yet</p>
            <p className="text-sm text-muted-foreground">Publish a startup to get matched with investors.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {sorted.map((match) => (
            <Card key={match.id}>
              <CardHeader className="flex flex-row items-start gap-4">
                <Avatar fallback={getInitials(match.investor_name)} className="h-10 w-10" />
                <div className="min-w-0 flex-1">
                  <CardTitle className="text-base">{match.investor_name}</CardTitle>
                  <p className="text-xs capitalize text-muted-foreground">
                    {humanize(match.investor_type) || "Investor"} &middot; for {match.startup_name}
                  </p>
                </div>
                <Badge variant={match.score >= 80 ? "success" : match.score >= 50 ? "warning" : "secondary"} className="shrink-0 px-3 py-1 text-sm">
                  {Math.round(match.score)}%
                </Badge>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  <Button size="sm" className="gap-1" asChild>
                    <Link href={`/chat?participant=${match.investor_id}`}><MessageSquare className="h-3.5 w-3.5" /> Message</Link>
                  </Button>
                  <Button size="sm" variant="outline" className="gap-1" onClick={() => setMeetingMatch(match)}>
                    <Calendar className="h-3.5 w-3.5" /> Schedule Meeting
                  </Button>
                  <Button size="sm" variant="outline" className="gap-1" asChild>
                    <Link href={`/founder/insights?match=${match.id}`}><Sparkles className="h-3.5 w-3.5" /> Explain this match</Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      <MeetingDialog open={!!meetingMatch} onOpenChange={() => setMeetingMatch(null)} investorId={meetingMatch?.investor_id} startupId={meetingMatch?.startup_id} />
    </div>
  )
}
