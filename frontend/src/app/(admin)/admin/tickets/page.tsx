"use client"

import { useState } from "react"
import {
  Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { useAdminTickets } from "@/hooks/use-api"
import { formatRelativeTime } from "@/lib/utils"
import { MessageSquare, User, AlertCircle, FileText } from "lucide-react"
import type { SupportTicket } from "@/types/api"

const priorityVariants: Record<string, "destructive" | "warning" | "default" | "secondary"> = {
  high: "destructive",
  medium: "warning",
  low: "default",
}

const statusVariants: Record<string, "default" | "secondary" | "success" | "outline"> = {
  open: "default",
  in_progress: "warning",
  resolved: "success",
  closed: "outline",
}

export default function AdminTicketsPage() {
  const [priorityFilter, setPriorityFilter] = useState<string>("all")
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const { data: tickets, isLoading } = useAdminTickets()

  const filtered = (tickets as SupportTicket[])?.filter((t) => {
    if (priorityFilter !== "all" && t.priority !== priorityFilter) return false
    if (statusFilter !== "all" && t.status !== statusFilter) return false
    return true
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Support Tickets</h1>
        <p className="text-muted-foreground">Manage customer support requests</p>
      </div>

      <div className="flex flex-wrap gap-2">
        <div className="flex gap-1 rounded-lg border p-1">
          {["all", "high", "medium", "low"].map((p) => (
            <Button
              key={p}
              variant={priorityFilter === p ? "default" : "ghost"}
              size="sm"
              onClick={() => setPriorityFilter(p)}
            >
              {p.charAt(0).toUpperCase() + p.slice(1)}
            </Button>
          ))}
        </div>
        <div className="flex gap-1 rounded-lg border p-1">
          {["all", "open", "in_progress", "resolved", "closed"].map((s) => (
            <Button
              key={s}
              variant={statusFilter === s ? "default" : "ghost"}
              size="sm"
              onClick={() => setStatusFilter(s)}
            >
              {s.replace("_", " ")}
            </Button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-40" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered?.map((ticket) => (
            <Card key={ticket.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <CardTitle className="text-base">{ticket.subject}</CardTitle>
                  <Badge variant={priorityVariants[ticket.priority] || "default"}>{ticket.priority}</Badge>
                </div>
                <CardDescription className="flex items-center gap-1">
                  <User className="h-3 w-3" />
                  {ticket.user_email}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-center gap-2 text-sm">
                  <FileText className="h-3 w-3 text-muted-foreground" />
                  <span className="text-muted-foreground">{ticket.category}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Badge variant={statusVariants[ticket.status] || "default"}>
                    {ticket.status.replace("_", " ")}
                  </Badge>
                  {ticket.assigned_to && (
                    <span className="text-xs text-muted-foreground flex items-center gap-1">
                      <User className="h-3 w-3" /> Assigned
                    </span>
                  )}
                </div>
              </CardContent>
              <CardFooter className="text-xs text-muted-foreground">
                {formatRelativeTime(ticket.created_at)}
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
