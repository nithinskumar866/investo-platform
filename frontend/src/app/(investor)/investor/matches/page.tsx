"use client"

import { useState } from "react"
import Link from "next/link"
import { toast } from "sonner"
import { useMatches, useSaveMatch } from "@/hooks/use-api"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { MeetingDialog } from "@/components/meetings/meeting-dialog"
import { Bookmark, Building2, MessageSquare, Calendar, Sparkles } from "lucide-react"
import { industryLabel, stageLabel } from "@/lib/constants"
import { formatCurrency } from "@/lib/utils"
import type { MatchScore } from "@/types/api"

export default function MatchesPage() {
  const { data: matches, isLoading } = useMatches("startup")
  const save = useSaveMatch()
  const [meetingMatch, setMeetingMatch] = useState<MatchScore | null>(null)

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-8 w-48" />
        {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-28" />)}
      </div>
    )
  }

  const sorted = [...(matches ?? [])].sort((a, b) => b.score - a.score)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Startup Matches</h1>
        <p className="text-muted-foreground">{sorted.length} matches based on your preferences</p>
      </div>

      {sorted.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center text-muted-foreground">
            <Sparkles className="mx-auto mb-2 h-8 w-8" />
            <p>No matches yet.</p>
            <p className="text-sm">Matches appear as founders publish startups that fit your preferences.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {sorted.map((m) => {
            const isSaved = m.is_bookmarked || m.status === "saved"
            return (
              <Card key={m.id} data-testid={`match-${m.id}`}>
                <CardContent className="flex flex-col gap-3 p-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="flex flex-1 items-start gap-3">
                    <Building2 className="mt-1 h-8 w-8 shrink-0 rounded-lg bg-primary/10 p-1.5 text-primary" />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <Link href={`/startup/${m.startup_id}`} className="font-semibold hover:underline">{m.startup_name}</Link>
                        <Badge variant={m.score >= 80 ? "success" : m.score >= 50 ? "warning" : "secondary"}>{Math.round(m.score)}% Match</Badge>
                      </div>
                      {m.startup_tagline && <p className="text-sm text-muted-foreground">{m.startup_tagline}</p>}
                      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                        <Badge variant="secondary" className="text-xs">{industryLabel(m.startup_industry)}</Badge>
                        <Badge variant="outline" className="text-xs">{stageLabel(m.startup_stage)}</Badge>
                        {m.startup_location && <span>{m.startup_location}</span>}
                        {m.startup_funding_goal && <span>Goal: {formatCurrency(m.startup_funding_goal)}</span>}
                      </div>
                    </div>
                  </div>
                  <div className="flex shrink-0 flex-wrap items-center gap-2">
                    <Button variant="outline" size="sm" asChild>
                      <Link href={`/investor/insights?match=${m.id}`}><Sparkles className="mr-1 h-3 w-3" /> Explain this match</Link>
                    </Button>
                    <Button variant="outline" size="sm" asChild>
                      <Link href={`/chat?participant=${m.startup_owner_id}`}><MessageSquare className="mr-1 h-3 w-3" /> Message</Link>
                    </Button>
                    <Button size="sm" onClick={() => setMeetingMatch(m)}>
                      <Calendar className="mr-1 h-3 w-3" /> Request Meeting
                    </Button>
                    <Button variant="ghost" size="sm" disabled={isSaved || save.isPending}
                      onClick={() => save.mutate(m.id, { onSuccess: () => toast.success(`${m.startup_name} saved`) })}>
                      <Bookmark className="mr-1 h-3 w-3" /> {isSaved ? "Saved" : "Save"}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
      <MeetingDialog open={!!meetingMatch} onOpenChange={() => setMeetingMatch(null)} match={meetingMatch ?? undefined} />
    </div>
  )
}
