"use client"

import Link from "next/link"
import { useSavedMatches } from "@/hooks/use-api"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Bookmark, MapPin, ExternalLink } from "lucide-react"
import { industryLabel, stageLabel } from "@/lib/constants"

export default function SavedPage() {
  const { data: saved, isLoading } = useSavedMatches()

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-44" />)}
        </div>
      </div>
    )
  }

  const rows = saved ?? []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Saved Startups</h1>
        <p className="text-muted-foreground">{rows.length} startup{rows.length !== 1 ? "s" : ""} saved</p>
      </div>

      {rows.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <Bookmark className="mb-2 h-10 w-10" />
            <p>No saved startups yet.</p>
            <p className="text-sm">Use Save on the Matches page to keep startups here.</p>
            <Button asChild className="mt-4">
              <Link href="/investor/matches">Go to Matches</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {rows.map((m) => (
            <Card key={m.id} className="h-full">
              <CardContent className="space-y-3 p-5">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <h3 className="font-semibold">{m.startup_name}</h3>
                    <p className="line-clamp-2 text-sm text-muted-foreground">{m.startup_tagline}</p>
                  </div>
                  <Badge variant={m.score >= 80 ? "success" : "secondary"} className="shrink-0">{Math.round(m.score)}%</Badge>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="secondary" className="text-xs">{industryLabel(m.startup_industry)}</Badge>
                  <Badge variant="outline" className="text-xs">{stageLabel(m.startup_stage)}</Badge>
                </div>
                {m.startup_location && (
                  <p className="flex items-center gap-1 text-xs text-muted-foreground">
                    <MapPin className="h-3 w-3" /> {m.startup_location}
                  </p>
                )}
                <Button variant="outline" size="sm" className="w-full" asChild>
                  <Link href={`/startup/${m.startup_id}`}>
                    <ExternalLink className="mr-1 h-3 w-3" /> View profile
                  </Link>
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
