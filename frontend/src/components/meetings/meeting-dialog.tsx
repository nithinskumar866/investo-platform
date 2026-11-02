"use client"

import { useEffect, useState } from "react"
import { toast } from "sonner"
import { Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Field } from "@/components/ui/field"
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog"
import { useCreateMeeting, useInvestors, useMatches, useMyStartups } from "@/hooks/use-api"
import { useAuthStore } from "@/stores/auth"
import { MEETING_TYPES } from "@/lib/constants"

function defaultStart() {
  const d = new Date(Date.now() + 24 * 60 * 60 * 1000)
  d.setMinutes(0, 0, 0)
  // datetime-local wants local time without a zone.
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
}

interface MeetingDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Founder flow: pre-select the investor (user id) and startup. */
  investorId?: number
  startupId?: number
  /** Investor flow: pre-select the startup. */
  match?: { startup_id: number; startup_owner_id: number; startup_name: string }
}

export function MeetingDialog(props: MeetingDialogProps) {
  const role = useAuthStore((s) => s.user?.role)
  if (!props.open) return null
  return role === "investor" ? <RequestForm {...props} /> : <ScheduleForm {...props} />
}

function ScheduleForm({ open, onOpenChange, investorId, startupId }: MeetingDialogProps) {
  const create = useCreateMeeting()
  const { data: investors } = useInvestors()
  const { data: startups } = useMyStartups()
  const { data: matches } = useMatches("investor")
  const [investor, setInvestor] = useState(investorId ? String(investorId) : "")
  const [startup, setStartup] = useState(startupId ? String(startupId) : "")
  const [title, setTitle] = useState("Intro call")
  const [type, setType] = useState("intro_call")
  const [start, setStart] = useState(defaultStart)
  const [duration, setDuration] = useState("30")

  // Suggest the startup this investor is matched with, as the API requires a match when one is set.
  useEffect(() => {
    if (startup || !investor) return
    const match = matches?.find((m) => m.investor_id === Number(investor))
    if (match) setStartup(String(match.startup_id))
  }, [investor, matches, startup])

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    const begin = new Date(start)
    create.mutate(
      {
        title: title.trim(),
        meeting_type: type,
        investor_id: Number(investor),
        startup: startup ? Number(startup) : null,
        scheduled_start: begin.toISOString(),
        scheduled_end: new Date(begin.getTime() + Number(duration) * 60000).toISOString(),
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      },
      {
        onSuccess: () => {
          toast.success("Meeting scheduled with a video link")
          onOpenChange(false)
        },
      },
    )
  }

  const investorOptions = (investors ?? []).map((i: any) => ({
    value: String(i.user.id),
    label: `${i.user.first_name} ${i.user.last_name}`.trim(),
  }))

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogTitle>Schedule a meeting</DialogTitle>
        <DialogDescription>A meet.jit.si video link is created automatically.</DialogDescription>
        <form onSubmit={submit} className="space-y-3">
          <Field label="Investor"><Select value={investor} onChange={(e) => setInvestor(e.target.value)} placeholder="Select investor" options={investorOptions} required /></Field>
          <Field label="Startup" hint="Needs an existing match with this investor. Leave empty for a general call.">
            <Select value={startup} onChange={(e) => setStartup(e.target.value)} placeholder="No specific startup"
              options={(startups ?? []).map((s) => ({ value: String(s.id), label: s.name }))} />
          </Field>
          <Field label="Title"><Input value={title} onChange={(e) => setTitle(e.target.value)} required /></Field>
          <Field label="Type"><Select value={type} onChange={(e) => setType(e.target.value)} options={MEETING_TYPES} /></Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Start"><Input type="datetime-local" value={start} onChange={(e) => setStart(e.target.value)} required /></Field>
            <Field label="Duration">
              <Select value={duration} onChange={(e) => setDuration(e.target.value)}
                options={[{ value: "15", label: "15 min" }, { value: "30", label: "30 min" }, { value: "60", label: "1 hour" }]} />
            </Field>
          </div>
          <Button type="submit" className="w-full" disabled={!investor || create.isPending}>
            {create.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Schedule meeting
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function RequestForm({ open, onOpenChange, match }: MeetingDialogProps) {
  const create = useCreateMeeting()
  const { data: matches } = useMatches("startup")
  const [matchKey, setMatchKey] = useState(match ? String(match.startup_id) : "")
  const [start, setStart] = useState(defaultStart)
  const [duration, setDuration] = useState("30")
  const [note, setNote] = useState("")

  const options = matches ?? (match ? [match] : [])
  const selected = options.find((m) => String(m.startup_id) === matchKey) ?? match

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selected) return
    const begin = new Date(start)
    create.mutate(
      {
        title: `Intro call: ${selected.startup_name}`,
        description: note.trim(),
        meeting_type: "intro_call",
        startup: selected.startup_id,
        scheduled_start: begin.toISOString(),
        scheduled_end: new Date(begin.getTime() + Number(duration) * 60000).toISOString(),
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      },
      {
        onSuccess: () => {
          toast.success("Meeting requested. The founder has been notified")
          onOpenChange(false)
        },
      },
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogTitle>Request a meeting</DialogTitle>
        <DialogDescription>A meet.jit.si video link is created automatically, and the founder is notified.</DialogDescription>
        <form onSubmit={submit} className="space-y-3">
          <Field label="Startup">
            <Select value={matchKey} onChange={(e) => setMatchKey(e.target.value)} placeholder="Select a matched startup"
              options={options.map((m) => ({ value: String(m.startup_id), label: m.startup_name }))} required />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Start"><Input type="datetime-local" value={start} onChange={(e) => setStart(e.target.value)} required /></Field>
            <Field label="Duration">
              <Select value={duration} onChange={(e) => setDuration(e.target.value)}
                options={[{ value: "15", label: "15 min" }, { value: "30", label: "30 min" }, { value: "60", label: "1 hour" }]} />
            </Field>
          </div>
          <Field label="Note (optional)"><Textarea value={note} onChange={(e) => setNote(e.target.value)} /></Field>
          <Button type="submit" className="w-full" disabled={!selected || create.isPending}>
            {create.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Request meeting
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}
