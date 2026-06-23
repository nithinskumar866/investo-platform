"use client"

import { useState } from "react"
import { useMeetings } from "@/hooks/use-api"
import { formatDate, formatRelativeTime } from "@/lib/utils"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Calendar, Clock, Users, Video, MapPin, CheckCircle, XCircle,
  CalendarDays, List,
} from "lucide-react"

const statusVariant: Record<string, "default" | "secondary" | "success" | "warning" | "destructive" | "outline"> = {
  scheduled: "default",
  confirmed: "success",
  pending: "warning",
  cancelled: "destructive",
  completed: "secondary",
}

function MeetingSkeleton() {
  return (
    <Card>
      <CardContent className="p-4">
        <Skeleton className="mb-2 h-5 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
        <div className="mt-3 flex gap-2">
          <Skeleton className="h-6 w-16 rounded-full" />
          <Skeleton className="h-6 w-16 rounded-full" />
        </div>
      </CardContent>
    </Card>
  )
}

export default function MeetingsPage() {
  const [tab, setTab] = useState<"upcoming" | "past">("upcoming")
  const [view, setView] = useState<"list" | "calendar">("list")
  const { data: meetings, isLoading } = useMeetings()

  const now = new Date()
  const filtered = meetings?.filter((m) => {
    const start = new Date(m.scheduled_start)
    return tab === "upcoming" ? start >= now : start < now
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-7 w-40" />
          <Skeleton className="h-9 w-48" />
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => <MeetingSkeleton key={i} />)}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <Calendar className="h-5 w-5 text-primary" />
          <h1 className="text-2xl font-bold">Meetings</h1>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex rounded-md border border-border">
            <Button
              variant={tab === "upcoming" ? "default" : "ghost"}
              size="sm"
              onClick={() => setTab("upcoming")}
              className="rounded-none rounded-l-md"
            >
              Upcoming
            </Button>
            <Button
              variant={tab === "past" ? "default" : "ghost"}
              size="sm"
              onClick={() => setTab("past")}
              className="rounded-none rounded-r-md"
            >
              Past
            </Button>
          </div>
          <div className="flex rounded-md border border-border">
            <Button
              variant={view === "list" ? "default" : "ghost"}
              size="icon"
              onClick={() => setView("list")}
              className="rounded-none rounded-l-md"
            >
              <List className="h-4 w-4" />
            </Button>
            <Button
              variant={view === "calendar" ? "default" : "ghost"}
              size="icon"
              onClick={() => setView("calendar")}
              className="rounded-none rounded-r-md"
            >
              <CalendarDays className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {view === "list" ? (
        <div className="grid gap-4 md:grid-cols-2">
          {filtered?.map((meeting) => (
            <Card key={meeting.id} className="transition-colors hover:bg-accent/50">
              <CardContent className="p-5">
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div className="min-w-0">
                    <h3 className="font-semibold truncate">{meeting.title}</h3>
                    <p className="mt-0.5 text-sm text-muted-foreground line-clamp-2">{meeting.description}</p>
                  </div>
                  <Badge variant={statusVariant[meeting.status] || "outline"} className="shrink-0">
                    {meeting.status}
                  </Badge>
                </div>

                <div className="space-y-1.5 text-sm text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4" />
                    <span>{formatDate(meeting.scheduled_start)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    <span>
                      {formatDate(meeting.scheduled_start, { hour: "2-digit", minute: "2-digit" })} -&nbsp;
                      {formatDate(meeting.scheduled_end, { hour: "2-digit", minute: "2-digit" })}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4" />
                    <span>Investor #{meeting.investor}{meeting.startup ? `, Startup #${meeting.startup}` : ""}</span>
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  {meeting.meeting_link && (
                    <Button variant="outline" size="sm" asChild>
                      <a href={meeting.meeting_link} target="_blank" rel="noopener noreferrer">
                        <Video className="mr-1.5 h-3.5 w-3.5" /> Join
                      </a>
                    </Button>
                  )}
                  {meeting.status === "pending" && (
                    <>
                      <Button variant="default" size="sm">
                        <CheckCircle className="mr-1.5 h-3.5 w-3.5" /> Confirm
                      </Button>
                      <Button variant="destructive" size="sm">
                        <XCircle className="mr-1.5 h-3.5 w-3.5" /> Cancel
                      </Button>
                    </>
                  )}
                  {meeting.status === "scheduled" && (
                    <Button variant="secondary" size="sm">
                      <XCircle className="mr-1.5 h-3.5 w-3.5" /> Cancel
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
          {filtered?.length === 0 && (
            <div className="col-span-2 flex flex-col items-center gap-2 py-16 text-muted-foreground">
              <Calendar className="h-12 w-12" />
              <p className="text-sm">No {tab} meetings found</p>
            </div>
          )}
        </div>
      ) : (
        <Card>
          <CardContent className="p-6">
            <div className="grid grid-cols-7 gap-px rounded-lg border border-border overflow-hidden text-center text-sm">
              {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((d) => (
                <div key={d} className="bg-muted p-2 text-xs font-medium text-muted-foreground">
                  {d}
                </div>
              ))}
              {Array.from({ length: 35 }).map((_, i) => {
                const day = i - 2
                const hasMeeting = filtered?.some((m) => {
                  const md = new Date(m.scheduled_start).getDate()
                  return md === day + 1
                })
                return (
                  <div
                    key={i}
                    className={`p-2 text-xs border-b border-r border-border/50 ${
                      day < 0 || day > 30 ? "text-muted-foreground/30" : "hover:bg-accent/50 cursor-pointer"
                    }`}
                  >
                    <span>{day >= 0 && day <= 30 ? day + 1 : ""}</span>
                    {hasMeeting && <div className="mx-auto mt-1 h-1.5 w-1.5 rounded-full bg-primary" />}
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
