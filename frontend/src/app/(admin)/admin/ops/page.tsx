"use client"

import { useState } from "react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useHealthCheck, useOpsAlerts, useOpsErrors, useSystemMetrics } from "@/hooks/use-api"
import { formatRelativeTime } from "@/lib/utils"
import { humanize } from "@/lib/constants"
import { AlertTriangle, CheckCircle, RefreshCw } from "lucide-react"

const SEVERITIES = ["all", "warning", "error", "critical"]

export default function AdminOpsPage() {
  const { data: health, isLoading: healthLoading } = useHealthCheck()
  const { data: metrics, isLoading: metricsLoading } = useSystemMetrics()
  const { data: alerts, refetch: refetchAlerts, isFetching: alertsFetching } = useOpsAlerts()
  const [severity, setSeverity] = useState("all")
  const { data: errors } = useOpsErrors(severity === "all" ? undefined : severity)

  if (healthLoading || metricsLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-28" />)}
        </div>
        <Skeleton className="h-72" />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Observability</h1>
          <p className="text-muted-foreground">System health, metrics, and alerting</p>
        </div>
        {health && <Badge variant={health.overall === "healthy" ? "success" : "warning"} data-testid="overall-health">Overall: {health.overall}</Badge>}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Object.entries(health?.services ?? {}).map(([key, svc]) => (
          <Card key={key} data-testid={`service-${key}`}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium capitalize text-muted-foreground">{humanize(key)}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-1">
              <div className="flex items-center gap-2">
                {svc.status === "healthy" ? <CheckCircle className="h-4 w-4 text-emerald-500" /> : <AlertTriangle className="h-4 w-4 text-amber-500" />}
                <span className="text-sm font-medium">{svc.status}</span>
              </div>
              <p className="truncate text-xs text-muted-foreground">{svc.detail}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Request metrics</CardTitle>
            <CardDescription>Since the metrics store last reset</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {metrics && (
              <>
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                  {[
                    ["Requests", metrics.api.total_requests],
                    ["Avg ms", metrics.api.avg_duration_ms],
                    ["Max ms", metrics.api.max_duration_ms],
                    ["Error rate", `${metrics.api.error_rate}%`],
                  ].map(([label, value]) => (
                    <div key={label}>
                      <p className="text-xs text-muted-foreground">{label}</p>
                      <p className="text-lg font-semibold">{value}</p>
                    </div>
                  ))}
                </div>
                <div>
                  <p className="mb-1 text-xs text-muted-foreground">Top endpoints</p>
                  <ul className="space-y-1 text-xs">
                    {metrics.api.top_endpoints.map((e) => (
                      <li key={e.endpoint} className="flex justify-between gap-2">
                        <span className="truncate font-mono">{e.endpoint}</span>
                        <span className="shrink-0 text-muted-foreground">{e.count} calls, {e.avg_duration} ms</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <p className="text-xs text-muted-foreground">
                  Active users (24h): {metrics.system.active_users_24h} &middot; Queue: {metrics.queue.total}
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-start justify-between">
            <div>
              <CardTitle>Alerts</CardTitle>
              <CardDescription>{alerts ? `${alerts.summary.triggered} triggered, ${alerts.summary.resolved} resolved` : "Loading..."}</CardDescription>
            </div>
            <Button variant="outline" size="sm" disabled={alertsFetching} onClick={() => refetchAlerts()}>
              <RefreshCw className="mr-1 h-3 w-3" /> Refresh
            </Button>
          </CardHeader>
          <CardContent>
            {!alerts?.alerts.length ? (
              <p className="py-8 text-center text-sm text-muted-foreground">No alerts have been raised.</p>
            ) : (
              <ul className="divide-y">
                {alerts.alerts.map((a) => (
                  <li key={a.id} className="flex items-center justify-between gap-2 py-2 text-sm">
                    <div className="min-w-0">
                      <p className="truncate font-medium">{a.rule_name}</p>
                      <p className="text-xs text-muted-foreground">{a.metric}: {a.metric_value} (limit {a.threshold})</p>
                    </div>
                    <Badge variant={a.status === "triggered" ? "destructive" : "secondary"}>{a.status}</Badge>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent errors</CardTitle>
          <CardDescription>{errors ? `${errors.summary.total} logged in total` : "Loading..."}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="mb-4 flex flex-wrap gap-2">
            {SEVERITIES.map((level) => (
              <Button key={level} variant={severity === level ? "default" : "outline"} size="sm" onClick={() => setSeverity(level)}>
                {level.charAt(0).toUpperCase() + level.slice(1)}
              </Button>
            ))}
          </div>
          {!errors?.errors.length ? (
            <div className="py-8 text-center text-sm text-muted-foreground">
              <CheckCircle className="mx-auto mb-2 h-6 w-6 text-emerald-500" />
              No errors logged
            </div>
          ) : (
            <ul className="divide-y">
              {errors.errors.map((err) => (
                <li key={err.id} className="flex items-start justify-between gap-3 py-3">
                  <div className="min-w-0">
                    <p className="text-sm font-medium">{err.message}</p>
                    <p className="text-xs text-muted-foreground">{err.source} &middot; {err.error_type}{err.user_email ? ` · ${err.user_email}` : ""}</p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <Badge variant={err.severity === "critical" || err.severity === "error" ? "destructive" : "secondary"}>{err.severity}</Badge>
                    <span className="text-xs text-muted-foreground">{formatRelativeTime(err.created_at)}</span>
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
