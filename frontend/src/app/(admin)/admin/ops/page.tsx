"use client"

import { useState } from "react"
import {
  Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useHealthCheck, useSystemMetrics } from "@/hooks/use-api"
import { formatRelativeTime } from "@/lib/utils"
import {
  Activity, Server, Database, Wifi, HardDrive, Cpu,
  AlertTriangle, CheckCircle, RefreshCw, Clock, BarChart3,
} from "lucide-react"

const serviceLabels: Record<string, { label: string; icon: typeof Server }> = {
  api: { label: "API Server", icon: Server },
  database: { label: "Database", icon: Database },
  redis: { label: "Redis", icon: Cpu },
  celery: { label: "Celery Workers", icon: Activity },
  storage: { label: "Storage", icon: HardDrive },
}

interface ErrorEntry {
  id: number
  service: string
  message: string
  level: string
  timestamp: string
}

export default function AdminOpsPage() {
  const { data: health, isLoading: healthLoading } = useHealthCheck()
  const { data: metrics, isLoading: metricsLoading } = useSystemMetrics()
  const [errorFilter, setErrorFilter] = useState<string>("all")

  const healthData = health as Record<string, { status: string; detail: string }> | undefined
  const sysMetrics = metrics as Record<string, unknown> | undefined
  const recentErrors = (sysMetrics?.recent_errors as ErrorEntry[]) ?? []

  const isLoading = healthLoading || metricsLoading

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <Skeleton className="h-72" />
          <Skeleton className="h-72" />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Observability</h1>
        <p className="text-muted-foreground">System health, metrics, and alerting</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {Object.entries(serviceLabels).map(([key, { label, icon: Icon }]) => {
          const svc = healthData?.[key]
          const isHealthy = svc?.status === "healthy" || svc?.status === "ok"
          return (
            <Card key={key}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
                <Icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent className="space-y-1">
                <div className="flex items-center gap-2">
                  {isHealthy ? (
                    <CheckCircle className="h-4 w-4 text-emerald-500" />
                  ) : (
                    <AlertTriangle className="h-4 w-4 text-destructive" />
                  )}
                  <span className="text-sm font-medium">{svc?.status ?? "unknown"}</span>
                </div>
                {svc?.detail && (
                  <p className="text-xs text-muted-foreground truncate">{svc.detail}</p>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Request Metrics</CardTitle>
            <CardDescription>API request rates and latencies</CardDescription>
          </CardHeader>
          <CardContent className="flex items-center justify-center h-60">
            <div className="text-center text-muted-foreground">
              <BarChart3 className="h-8 w-8 mx-auto mb-2" />
              <p className="text-sm">Chart placeholder</p>
              {sysMetrics?.api && (
                <div className="mt-4 space-y-1 text-xs">
                  {Object.entries(sysMetrics.api as Record<string, unknown>).map(([k, v]) => (
                    <p key={k} className="capitalize">{k.replace("_", " ")}: {String(v)}</p>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Alert Rules</CardTitle>
            <CardDescription>Active monitoring alerts</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { rule: "High error rate (>5%)", severity: "critical", status: "triggered" },
              { rule: "API latency > 500ms", severity: "warning", status: "ok" },
              { rule: "Database connection pool exhaustion", severity: "critical", status: "ok" },
              { rule: "Celery queue backlog > 1000", severity: "warning", status: "ok" },
              { rule: "Disk usage > 80%", severity: "info", status: "ok" },
            ].map((alert, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={`h-2 w-2 rounded-full ${
                    alert.status === "triggered" ? "bg-destructive" : "bg-emerald-500"
                  }`} />
                  <p className="text-sm">{alert.rule}</p>
                </div>
                <Badge variant={alert.severity === "critical" ? "destructive" : alert.severity === "warning" ? "warning" : "default"}>
                  {alert.severity}
                </Badge>
              </div>
            ))}
          </CardContent>
          <CardFooter>
            <Button variant="outline" size="sm" className="w-full">
              <RefreshCw className="h-4 w-4 mr-2" /> Refresh Alerts
            </Button>
          </CardFooter>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Errors</CardTitle>
          <CardDescription>Latest system errors and exceptions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 mb-4">
            {["all", "error", "warning", "critical"].map((level) => (
              <Button
                key={level}
                variant={errorFilter === level ? "default" : "outline"}
                size="sm"
                onClick={() => setErrorFilter(level)}
              >
                {level.charAt(0).toUpperCase() + level.slice(1)}
              </Button>
            ))}
          </div>
          <div className="divide-y">
            {recentErrors
              .filter((e) => errorFilter === "all" || e.level === errorFilter)
              .map((err) => (
                <div key={err.id} className="flex items-start justify-between py-3">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className={`h-4 w-4 mt-0.5 ${
                      err.level === "critical" ? "text-destructive" : err.level === "warning" ? "text-amber-500" : "text-muted-foreground"
                    }`} />
                    <div>
                      <p className="text-sm font-medium">{err.message}</p>
                      <p className="text-xs text-muted-foreground">{err.service}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Badge variant={err.level === "critical" ? "destructive" : err.level === "warning" ? "warning" : "default"}>
                      {err.level}
                    </Badge>
                    <span className="text-xs text-muted-foreground">{formatRelativeTime(err.timestamp)}</span>
                  </div>
                </div>
              ))}
            {recentErrors.length === 0 && (
              <div className="py-8 text-center text-sm text-muted-foreground">
                <CheckCircle className="h-6 w-6 mx-auto mb-2 text-emerald-500" />
                No recent errors
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
