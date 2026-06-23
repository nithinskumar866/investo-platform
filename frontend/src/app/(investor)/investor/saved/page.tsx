"use client"

import { useMatches } from "@/hooks/use-api"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Bookmark, MapPin, ExternalLink } from "lucide-react"
import Link from "next/link"

export default function SavedPage() {
  const { data: matches, isLoading } = useMatches("startup")

  const saved = (matches ?? []).filter((m) => m.is_bookmarked)

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64 mt-2" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6 space-y-3">
                <Skeleton className="h-5 w-3/4" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-1/2" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Saved Startups</h1>
        <p className="text-muted-foreground">
          {saved.length} startup{saved.length !== 1 ? "s" : ""} bookmarked
        </p>
      </div>

      {saved.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <Bookmark className="mb-2 h-10 w-10" />
            <p>No saved startups yet.</p>
            <p className="text-sm">Bookmark startups from the Discover page to view them here.</p>
            <Button asChild className="mt-4">
              <Link href="/investor/discover">Discover Startups</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {saved.map((m) => {
            const s = m.startup_detail
            if (!s) return null
            return (
              <Card key={m.id} className="h-full">
                <CardContent className="p-5 space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold">{s.name}</h3>
                      <p className="text-sm text-muted-foreground line-clamp-2">{s.tagline}</p>
                    </div>
                    <Badge variant={m.score >= 80 ? "success" : "secondary"} className="shrink-0">
                      {Math.round(m.score)}%
                    </Badge>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="secondary" className="text-xs">{s.industry}</Badge>
                    <Badge variant="outline" className="text-xs">{s.stage}</Badge>
                  </div>
                  {s.location && (
                    <p className="flex items-center gap-1 text-xs text-muted-foreground">
                      <MapPin className="h-3 w-3" /> {s.location}
                    </p>
                  )}
                  <Button variant="outline" size="sm" className="w-full" asChild>
                    <Link href={`/startup/${s.slug}`}>
                      <ExternalLink className="mr-1 h-3 w-3" /> View Profile
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
