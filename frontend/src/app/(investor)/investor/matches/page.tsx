"use client"

import { useState } from "react"
import { useMatches } from "@/hooks/use-api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Avatar } from "@/components/ui/avatar"
import { Building2, MessageSquare, Calendar, Sparkles, ChevronDown, ChevronUp } from "lucide-react"
import Link from "next/link"

export default function MatchesPage() {
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const { data: matches, isLoading } = useMatches("startup")

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64 mt-2" />
        </div>
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-4 w-1/2 mt-2" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  const sorted = [...(matches ?? [])].sort((a, b) => b.score - a.score)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Startup Matches</h1>
        <p className="text-muted-foreground">{sorted.length} potential matches based on your preferences</p>
      </div>

      {sorted.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center text-muted-foreground">
            <Sparkles className="mx-auto mb-2 h-8 w-8" />
            <p>No matches yet.</p>
            <p className="text-sm">Update your investor profile to improve matching.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {sorted.map((m) => {
            const expanded = expandedId === m.id

            return (
              <Card key={m.id}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1">
                      <Building2 className="mt-1 h-8 w-8 rounded-lg bg-primary/10 p-1.5 text-primary" />
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold">{m.startup_name ?? `Startup #${m.startup}`}</h3>
                          <Badge
                            variant={m.score >= 80 ? "success" : m.score >= 50 ? "warning" : "secondary"}
                          >
                            {Math.round(m.score)}% Match
                          </Badge>
                          {m.status === "pending" && <Badge variant="outline">New</Badge>}
                        </div>
                        {m.startup_tagline && (
                          <p className="text-sm text-muted-foreground">{m.startup_tagline}</p>
                        )}
                        <div className="flex flex-wrap gap-2 mt-2">
                          <Badge variant="secondary" className="text-xs">{m.startup_industry}</Badge>
                          <Badge variant="outline" className="text-xs">{m.startup_stage}</Badge>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <Button variant="outline" size="sm" asChild>
                        <Link href={`/chat?participant=${m.startup_owner_id}`} className="message-startup-btn">
                          <MessageSquare className="mr-1 h-3 w-3" /> Message
                        </Link>
                      </Button>
                      <Button size="sm">
                        <Calendar className="mr-1 h-3 w-3" /> Request Meeting
                      </Button>
                      <Button variant="ghost" size="icon" onClick={() => setExpandedId(expanded ? null : m.id)}>
                        {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>

                  {expanded && (
                    <div className="mt-4 border-t pt-4 space-y-3">
                      <div className="grid gap-3 sm:grid-cols-2">
                        <div>
                          <p className="text-xs text-muted-foreground">Location</p>
                          <p className="text-sm">{m.startup_location || "N/A"}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Team Size</p>
                          <p className="text-sm">{"N/A"}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Funding Goal</p>
                          <p className="text-sm">{m.startup_funding_goal ? `$${Number(m.startup_funding_goal).toLocaleString()}` : "N/A"}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Valuation</p>
                          <p className="text-sm">{"N/A"}</p>
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground line-clamp-3">{m.startup_tagline}</p>
                      <Button variant="outline" size="sm" asChild>
                        <Link href={`/startup/${m.startup_slug}`}>View Full Profile</Link>
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
