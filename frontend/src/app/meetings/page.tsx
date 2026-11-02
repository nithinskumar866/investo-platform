"use client"

import { useState } from "react"
import { toast } from "sonner"
import { useMeetingAction, useMeetings } from "@/hooks/use-api"
import { useAuthStore } from "@/stores/auth"
import { cn, formatDate } from "@/lib/utils"
import { humanize } from "@/lib/constants"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { MeetingDialog } from "@/components/meetings/meeting-dialog"
import {
  Calendar, CalendarDays, CheckCircle, ChevronLeft, ChevronRight, Clock, List, Plus, Users, Video, XCircle,
} from "lucide-react"
import type { Meeting } from "@/types/api"

const statusVariant: Record<string, "default" | "secondary" | "success" | "destructive"> = {
  scheduled: "default",
  confirmed: "success",
  cancelled: "destructive",
  completed: "secondary",
}

const timeFormat: Intl.DateTimeFormatOptions = { hour: "2-digit", minute: "2-digit" }

function MeetingCard({ meeting }: { meeting: Meeting }) {
  const me = useAuthStore((s) => s.user)
  const action = useMeetingAction()
  const open = meeting.status === "scheduled" || meeting.status === "confirmed"
  const isPast = new Date(meeting.scheduled_start) < new Date()

  const run = (name: "confirm" | "cancel" | "complete", message: string) =>
    action.mutate({ id: meeting.id, action: name }, { onSuccess: () => toast.success(message) })

  return (
    <Card data-testid={`meeting-${meeting.id}`}>
      <CardContent className="p-5">
        <div className="mb-3 flex items-start justify-between gap-2">
          <div className="min-w-0">
            <h3 className="truncate font-semibold">{meeting.title}</h3>
            <p className="mt-0.5 text-sm capitalize text-muted-foreground">{humanize(meeting.meeting_type)}</p>
          </div>
          <Badge variant={statusVariant[meeting.status] || "default"} className="shrink-0">{meeting.status}</Badge>
        </div>

        <div className="space-y-1.5 text-sm text-muted-foreground">
          <div className="flex items-center gap-2"><Calendar className="h-4 w-4" /><span>{formatDate(meeting.scheduled_start)}</span></div>
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            <span>{formatDate(meeting.scheduled_start, timeFormat)} to {formatDate(meeting.scheduled_end, timeFormat)}</span>
          </div>
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 shrink-0" />
            <span className="truncate">
              {meeting.organizer === me?.id ? meeting.investor_email : meeting.organizer_email}
              {meeting.startup_name ? `, ${meeting.startup_name}` : ""}
            </span>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          {meeting.meeting_link && open && (
            <Button variant="outline" size="sm" asChild>
              <a href={meeting.meeting_link} target="_blank" rel="noopener noreferrer">
                <Video className="mr-1.5 h-3.5 w-3.5" /> Join
              </a>
            </Button>
          )}
          {meeting.status === "scheduled" && meeting.organizer !== me?.id && (
            <Button size="sm" disabled={action.isPending} onClick={() => run("confirm", "Meeting confirmed")}>
              <CheckCircle className="mr-1.5 h-3.5 w-3.5" /> Confirm
            </Button>
          )}
          {open && isPast && (
            <Button variant="secondary" size="sm" disabled={action.isPending} onClick={() => run("complete", "Meeting marked complete")}>
              Mark complete
            </Button>
          )}
          {open && (
            <Button variant="ghost" size="sm" className="text-destructive" disabled={action.isPending}
              onClick={() => { if (confirm("Cancel this meeting?")) run("cancel", "Meeting cancelled") }}>
              <XCircle className="mr-1.5 h-3.5 w-3.5" /> Cancel
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

function MonthView({ meetings }: { meetings: Meeting[] }) {
  const [cursor, setCursor] = useState(() => {
    const now = new Date()
    return new Date(now.getFullYear(), now.getMonth(), 1)
  })
  const year = cursor.getFullYear()
  const month = cursor.getMonth()
  const leadingBlanks = new Date(year, month, 1).getDay()
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const today = new Date()

  return (
    <Card>
      <CardContent className="p-4 sm:p-6">
        <div className="mb-4 flex items-center justify-between">
          <Button variant="ghost" size="icon" aria-label="Previous month" onClick={() => setCursor(new Date(year, month - 1, 1))}><ChevronLeft className="h-4 w-4" /></Button>
          <h2 className="font-semibold" data-testid="calendar-month">{formatDate(cursor, { month: "long", year: "numeric" })}</h2>
          <Button variant="ghost" size="icon" aria-label="Next month" onClick={() => setCursor(new Date(year, month + 1, 1))}><ChevronRight className="h-4 w-4" /></Button>
        </div>
        <div className="grid grid-cols-7 overflow-hidden rounded-lg border text-sm">
          {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((d) => (
            <div key={d} className="bg-muted p-2 text-center text-xs font-medium text-muted-foreground">{d}</div>
          ))}
          {Array.from({ length: leadingBlanks }).map((_, i) => <div key={`blank-${i}`} className="border-t border-border/50" />)}
          {Array.from({ length: daysInMonth }).map((_, i) => {
            const day = i + 1
            const events = meetings.filter((m) => {
              const d = new Date(m.scheduled_start)
              return d.getFullYear() === year && d.getMonth() === month && d.getDate() === day
            })
            const isToday = today.getFullYear() === year && today.getMonth() === month && today.getDate() === day
            return (
              <div key={day} className="min-h-[72px] space-y-1 border-l border-t border-border/50 p-1.5 first:border-l-0">
                <span className={cn("text-xs", isToday && "rounded bg-primary px-1 font-semibold text-primary-foreground")}>{day}</span>
                {events.map((m) => (
                  <p key={m.id} title={m.title} className={cn("truncate rounded bg-primary/15 px-1 text-[11px]", m.status === "cancelled" && "line-through opacity-60")}>
                    {formatDate(m.scheduled_start, timeFormat)} {m.title}
                  </p>
                ))}
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

export default function MeetingsPage() {
  const role = useAuthStore((s) => s.user?.role)
  const [tab, setTab] = useState<"upcoming" | "past">("upcoming")
  const [view, setView] = useState<"list" | "calendar">("list")
  const [dialogOpen, setDialogOpen] = useState(false)
  const { data: meetings, isLoading } = useMeetings()

  const now = new Date()
  const filtered = (meetings ?? [])
    .filter((m) => (tab === "upcoming" ? new Date(m.scheduled_start) >= now : new Date(m.scheduled_start) < now))
    .sort((a, b) => {
      const diff = new Date(a.scheduled_start).getTime() - new Date(b.scheduled_start).getTime()
      return tab === "upcoming" ? diff : -diff
    })

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <Calendar className="h-5 w-5 text-primary" />
          <h1 className="text-2xl font-bold">Meetings</h1>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {view === "list" && (
            <div className="flex rounded-md border border-border">
              <Button variant={tab === "upcoming" ? "default" : "ghost"} size="sm" onClick={() => setTab("upcoming")} className="rounded-none rounded-l-md">Upcoming</Button>
              <Button variant={tab === "past" ? "default" : "ghost"} size="sm" onClick={() => setTab("past")} className="rounded-none rounded-r-md">Past</Button>
            </div>
          )}
          <div className="flex rounded-md border border-border">
            <Button variant={view === "list" ? "default" : "ghost"} size="icon" aria-label="List view" onClick={() => setView("list")} className="rounded-none rounded-l-md"><List className="h-4 w-4" /></Button>
            <Button variant={view === "calendar" ? "default" : "ghost"} size="icon" aria-label="Calendar view" onClick={() => setView("calendar")} className="rounded-none rounded-r-md"><CalendarDays className="h-4 w-4" /></Button>
          </div>
          {role !== "admin" && (
            <Button onClick={() => setDialogOpen(true)}>
              <Plus className="mr-1 h-4 w-4" /> {role === "investor" ? "Request meeting" : "New meeting"}
            </Button>
          )}
        </div>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-44" />)}
        </div>
      ) : view === "calendar" ? (
        <MonthView meetings={meetings ?? []} />
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-16 text-muted-foreground">
          <Calendar className="h-12 w-12" />
          <p className="text-sm">No {tab} meetings</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {filtered.map((meeting) => <MeetingCard key={meeting.id} meeting={meeting} />)}
        </div>
      )}
      <MeetingDialog open={dialogOpen} onOpenChange={setDialogOpen} />
    </div>
  )
}
