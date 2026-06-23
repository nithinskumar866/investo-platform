"use client"

import { useState } from "react"
import {
  Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar } from "@/components/ui/avatar"
import { Skeleton } from "@/components/ui/skeleton"
import { formatCurrency, formatRelativeTime } from "@/lib/utils"
import {
  AlertTriangle, Ban, Eye, Search, ShieldAlert, UserX, Activity,
} from "lucide-react"

interface FlaggedActivity {
  id: number
  type: string
  description: string
  severity: "low" | "medium" | "high" | "critical"
  user: { name: string; email: string; avatar: string | null }
  created_at: string
}

const severityVariants: Record<string, "default" | "warning" | "destructive" | "success"> = {
  low: "default",
  medium: "warning",
  high: "destructive",
  critical: "destructive",
}

const flaggedActivities: FlaggedActivity[] = [
  { id: 1, type: "Unusual Login", description: "Login from new IP in different country", severity: "high", user: { name: "Mike Ross", email: "mike@example.com", avatar: null }, created_at: new Date().toISOString() },
  { id: 2, type: "Bulk Action", description: "Bulk export of startup data", severity: "medium", user: { name: "Rachel Zane", email: "rachel@example.com", avatar: null }, created_at: new Date().toISOString() },
  { id: 3, type: "Suspicious Payment", description: "Multiple failed payment attempts", severity: "critical", user: { name: "Louis Litt", email: "louis@example.com", avatar: null }, created_at: new Date().toISOString() },
]

export default function AdminRiskPage() {
  const [tab, setTab] = useState<"flagged" | "patterns" | "suspicious">("flagged")

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Risk Monitoring</h1>
        <p className="text-muted-foreground">Detect unusual activity and potential threats</p>
      </div>

      <div className="flex gap-1 rounded-lg border p-1 w-fit">
        {[
          { key: "flagged", label: "Flagged Activities", icon: AlertTriangle },
          { key: "patterns", label: "Unusual Patterns", icon: Activity },
          { key: "suspicious", label: "Suspicious Accounts", icon: UserX },
        ].map(({ key, label, icon: Icon }) => (
          <Button
            key={key}
            variant={tab === key ? "default" : "ghost"}
            size="sm"
            onClick={() => setTab(key)}
          >
            <Icon className="h-4 w-4 mr-1" />
            {label}
          </Button>
        ))}
      </div>

      {tab === "flagged" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">{flaggedActivities.length} flagged activities</p>
            <Button variant="outline" size="sm">Mark All Reviewed</Button>
          </div>
          {flaggedActivities.map((activity) => (
            <Card key={activity.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <ShieldAlert className={`h-5 w-5 ${activity.severity === "critical" || activity.severity === "high" ? "text-destructive" : "text-amber-500"}`} />
                    <div>
                      <CardTitle className="text-base">{activity.type}</CardTitle>
                      <CardDescription>{activity.description}</CardDescription>
                    </div>
                  </div>
                  <Badge variant={severityVariants[activity.severity]}>{activity.severity}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2 text-sm">
                  <Avatar src={activity.user.avatar || undefined} fallback={activity.user.name.split(" ").map(n => n[0]).join("")} />
                  <span>{activity.user.name}</span>
                  <span className="text-muted-foreground">{activity.user.email}</span>
                </div>
              </CardContent>
              <CardFooter className="flex justify-between">
                <span className="text-xs text-muted-foreground">{formatRelativeTime(activity.created_at)}</span>
                <div className="flex gap-1">
                  <Button variant="ghost" size="sm"><Eye className="h-4 w-4 mr-1" /> Review</Button>
                  <Button variant="ghost" size="sm"><Ban className="h-4 w-4 mr-1" /> Dismiss</Button>
                </div>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {tab === "patterns" && (
        <Card>
          <CardHeader>
            <CardTitle>Unusual Patterns</CardTitle>
            <CardDescription>Anomaly detection insights</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              { pattern: "Rapid account creation", count: 12, threat: "medium", period: "Last hour" },
              { pattern: "Concurrent logins from multiple IPs", count: 3, threat: "high", period: "Last 24h" },
              { pattern: "Unusual data access frequency", count: 8, threat: "low", period: "Last 7 days" },
            ].map((p, i) => (
              <div key={i} className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">{p.pattern}</p>
                  <p className="text-xs text-muted-foreground">{p.count} instances &middot; {p.period}</p>
                </div>
                <Badge variant={p.threat === "high" ? "destructive" : p.threat === "medium" ? "warning" : "default"}>
                  {p.threat}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {tab === "suspicious" && (
        <Card>
          <CardHeader>
            <CardTitle>Suspicious Accounts Queue</CardTitle>
            <CardDescription>Accounts flagged for review</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="divide-y">
              {[
                { name: "John Doe", email: "john.doe@spam.com", reason: "Unverified email domain", risk: "high" },
                { name: "Jane Smith", email: "jane.smith@temp.com", reason: "Temporary email provider", risk: "medium" },
              ].map((acc, i) => (
                <div key={i} className="flex items-center justify-between py-3">
                  <div className="flex items-center gap-3">
                    <Avatar fallback={acc.name.split(" ").map(n => n[0]).join("")} />
                    <div>
                      <p className="text-sm font-medium">{acc.name}</p>
                      <p className="text-xs text-muted-foreground">{acc.email} &middot; {acc.reason}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={acc.risk === "high" ? "destructive" : "warning"}>{acc.risk} risk</Badge>
                    <Button variant="ghost" size="sm">Review</Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
