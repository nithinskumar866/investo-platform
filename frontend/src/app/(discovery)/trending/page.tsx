"use client"

import Link from "next/link"
import { useStartups, useTrendingFeed } from "@/hooks/use-api"
import { formatRelativeTime } from "@/lib/utils"
import { stageLabel } from "@/lib/constants"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Activity, ArrowUpRight, Bookmark, Eye, TrendingUp } from "lucide-react"
import type { Startup } from "@/types/api"

const PUBLIC = ["active", "funded"]

function Ranked({ rows, metric }: { rows: Startup[]; metric: (s: Startup) => string }) {
  if (rows.length === 0) return <p className="py-6 text-center text-sm text-muted-foreground">Nothing to rank yet.</p>
  return (
    <div className="space-y-3">
      {rows.map((s, i) => (
        <Link key={s.id} href={`/startup/${s.id}`} className="block">
          <Card className="transition-colors hover:bg-accent/10">
            <CardContent className="flex items-center gap-3 p-4">
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">{i + 1}</span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="truncate text-sm font-medium">{s.name}</p>
                  <Badge variant="secondary" className="shrink-0 text-xs">{stageLabel(s.stage)}</Badge>
                </div>
                <p className="truncate text-xs text-muted-foreground">{metric(s)}</p>
              </div>
              <ArrowUpRight className="h-4 w-4 shrink-0 text-muted-foreground" />
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  )
}

export default function TrendingPage() {
  const { data: byViews, isLoading: viewsLoading } = useStartups({ ordering: "-view_count", per_page: 50 })
  const { data: feed, isLoading: feedLoading } = useTrendingFeed()

  const published = (byViews ?? []).filter((s) => PUBLIC.includes(s.status))
  const mostViewed = published.slice(0, 5)
  const mostSaved = [...published].filter((s) => s.bookmark_count > 0).sort((a, b) => b.bookmark_count - a.bookmark_count).slice(0, 5)

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-primary" />
            Trending Now
          </CardTitle>
        </CardHeader>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        <section>
          <h2 className="mb-3 flex items-center gap-2 font-semibold"><Eye className="h-4 w-4 text-primary" /> Most viewed startups</h2>
          {viewsLoading ? <Skeleton className="h-48" /> : <Ranked rows={mostViewed} metric={(s) => `${s.view_count} views`} />}
        </section>

        <section>
          <h2 className="mb-3 flex items-center gap-2 font-semibold"><Bookmark className="h-4 w-4 text-primary" /> Most bookmarked startups</h2>
          {viewsLoading ? <Skeleton className="h-48" /> : <Ranked rows={mostSaved} metric={(s) => `${s.bookmark_count} bookmarks`} />}
        </section>

        <section>
          <h2 className="mb-3 flex items-center gap-2 font-semibold"><Activity className="h-4 w-4 text-primary" /> Trending activity</h2>
          {feedLoading ? (
            <Skeleton className="h-48" />
          ) : !feed?.length ? (
            <p className="py-6 text-center text-sm text-muted-foreground">No recent activity.</p>
          ) : (
            <div className="space-y-3">
              {feed.map((item) => (
                <Card key={item.id}>
                  <CardContent className="p-4">
                    <p className="text-sm font-medium">{item.title}</p>
                    <p className="text-xs text-muted-foreground">{formatRelativeTime(item.created_at)}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
