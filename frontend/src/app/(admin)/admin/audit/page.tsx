"use client"

import { useState } from "react"
import {
  Card, CardHeader, CardTitle, CardDescription, CardContent,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { useAdminAuditLogs } from "@/hooks/use-api"
import { formatRelativeTime } from "@/lib/utils"
import { Search, Clock } from "lucide-react"
import type { AuditLog } from "@/types/api"

const ACTION_TYPES = [
  "user_suspend", "user_restore", "user_ban", "startup_approve", "startup_reject", "startup_archive",
  "startup_flag", "verification_change", "subscription_change", "ticket_action",
]

function actionVariant(action: string): "default" | "destructive" | "warning" | "success" {
  if (/approve|restore/.test(action)) return "success"
  if (/ban|suspend|reject/.test(action)) return "destructive"
  if (/flag|archive/.test(action)) return "warning"
  return "default"
}

export default function AdminAuditPage() {
  const [actionFilter, setActionFilter] = useState<string>("all")
  const [searchQuery, setSearchQuery] = useState("")
  const { data: logs, isLoading } = useAdminAuditLogs({ action_type: actionFilter !== "all" ? actionFilter : undefined })

  const filtered = (logs as AuditLog[])?.filter((log) => {
    if (!searchQuery) return true
    const q = searchQuery.toLowerCase()
    return (
      (log.actor_email ?? "").toLowerCase().includes(q) ||
      log.target_repr.toLowerCase().includes(q) ||
      log.description.toLowerCase().includes(q)
    )
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Audit Logs</h1>
        <p className="text-muted-foreground">Track all administrative actions</p>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            aria-label="Search audit logs"
            placeholder="Search actor, target, or description..."
            className="pl-9"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <Select
          aria-label="Filter by action"
          className="sm:w-64"
          value={actionFilter === "all" ? "" : actionFilter}
          onChange={(e) => setActionFilter(e.target.value || "all")}
          placeholder="All actions"
          options={ACTION_TYPES.map((a) => ({ value: a, label: a.replace(/_/g, " ") }))}
        />
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-14 w-full" />
          ))}
        </div>
      ) : (
        <Card>
          <div className="divide-y">
            {filtered?.map((log) => (
              <div key={log.id} className="flex items-center justify-between p-4">
                <div className="flex items-start gap-3">
                  <Clock className="h-4 w-4 mt-0.5 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium">{log.description}</p>
                    <p className="text-xs text-muted-foreground">
                      {log.actor_email ?? "System"} &middot; {log.target_type}: {log.target_repr}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <Badge variant={actionVariant(log.action_type)}>
                    {log.action_type.replace(/_/g, " ")}
                  </Badge>
                  <span className="text-xs text-muted-foreground whitespace-nowrap">
                    {formatRelativeTime(log.created_at)}
                  </span>
                </div>
              </div>
            ))}
            {(!filtered || filtered.length === 0) && (
              <div className="p-8 text-center text-sm text-muted-foreground">
                No audit logs found
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  )
}
