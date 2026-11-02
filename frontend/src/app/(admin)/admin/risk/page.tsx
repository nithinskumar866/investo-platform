"use client"

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { useAdminRisk } from "@/hooks/use-api"
import { Activity, MessageSquare, UserX } from "lucide-react"

export default function AdminRiskPage() {
  const { data, isLoading } = useAdminRisk()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Risk Monitoring</h1>
        <p className="text-muted-foreground">Activity over the last 24 hours that crosses the backend&apos;s risk thresholds</p>
      </div>

      {isLoading || !data ? (
        <div className="grid gap-4 md:grid-cols-3">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-40" />)}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base"><UserX className="h-4 w-4" /> Suspensions (24h)</CardTitle>
            </CardHeader>
            <CardContent>
              <span className="text-3xl font-bold" data-testid="recent-bans">{data.recent_bans_24h}</span>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base"><MessageSquare className="h-4 w-4" /> Excessive messaging</CardTitle>
              <CardDescription>More than 100 messages in 24 hours</CardDescription>
            </CardHeader>
            <CardContent>
              {data.excessive_messaging.length === 0 ? (
                <p className="text-sm text-muted-foreground">No accounts flagged.</p>
              ) : (
                <ul className="divide-y">
                  {data.excessive_messaging.map((row) => (
                    <li key={row.sender_id} className="flex items-center justify-between gap-2 py-2 text-sm">
                      <span className="truncate">{row.sender__email}</span>
                      <Badge variant="destructive">{row.msg_count}</Badge>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base"><Activity className="h-4 w-4" /> Rapid activity</CardTitle>
              <CardDescription>More than 50 feed events in 24 hours</CardDescription>
            </CardHeader>
            <CardContent>
              {data.rapid_activity.length === 0 ? (
                <p className="text-sm text-muted-foreground">No accounts flagged.</p>
              ) : (
                <ul className="divide-y">
                  {data.rapid_activity.map((row) => (
                    <li key={row.actor_id} className="flex items-center justify-between gap-2 py-2 text-sm">
                      <span className="truncate">{row.actor__email}</span>
                      <Badge variant="warning">{row.activity_count}</Badge>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
