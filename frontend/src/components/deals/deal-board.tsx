"use client"

import { useState } from "react"
import Link from "next/link"
import { toast } from "sonner"
import { ArrowRight, Building2, CheckCircle2, ExternalLink, Loader2, User, XCircle } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Field } from "@/components/ui/field"
import { Skeleton } from "@/components/ui/skeleton"
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog"
import { useDealAction, useDealDetail } from "@/hooks/use-api"
import { DEAL_STAGES, dealStageLabel } from "@/lib/constants"
import { formatCurrency } from "@/lib/utils"
import type { Deal } from "@/types/api"

type Side = "investor" | "startup"

/** The stage move_stage may go to next. Term sheet and close have their own actions. */
const NEXT_STAGE: Record<string, string> = {
  interested: "meeting_scheduled",
  meeting_scheduled: "due_diligence",
  due_diligence: "negotiating",
}

const OPEN_STAGES = ["interested", "meeting_scheduled", "due_diligence", "negotiating", "term_sheet_sent"]

function money(v: Deal["amount_offered"]) {
  return v === null || v === undefined ? null : formatCurrency(v)
}

function AmountDialog({ deal, side, kind, onClose }: { deal: Deal; side: Side; kind: "term_sheet" | "close"; onClose: () => void }) {
  const action = useDealAction(side)
  const [amount, setAmount] = useState(deal.amount_offered ? String(Number(deal.amount_offered)) : deal.amount_requested ? String(Number(deal.amount_requested)) : "")
  const [equity, setEquity] = useState(deal.equity_offered ? String(Number(deal.equity_offered)) : "")
  const [url, setUrl] = useState("")

  const isClose = kind === "close"

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    const body: Record<string, unknown> = { amount_offered: amount }
    if (equity) body.equity_offered = equity
    if (url.trim()) body.term_sheet_url = url.trim()
    action.mutate(
      { id: deal.id, action: isClose ? "mark_invested" : "send_term_sheet", body },
      {
        onSuccess: () => {
          toast.success(isClose ? "Deal closed. Funding progress updated." : "Term sheet sent to the founder")
          onClose()
        },
      },
    )
  }

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent>
        <DialogTitle>{isClose ? `Close deal with ${deal.startup.name}` : `Send term sheet to ${deal.startup.name}`}</DialogTitle>
        <DialogDescription>Dummy money only: nothing is charged or transferred.</DialogDescription>
        <form onSubmit={submit} className="space-y-3">
          <Field label={isClose ? "Final amount ($)" : "Amount offered ($)"}>
            <Input type="number" min="1" step="0.01" required value={amount} onChange={(e) => setAmount(e.target.value)} />
          </Field>
          <Field label="Equity (%)"><Input type="number" min="0" max="100" step="0.01" value={equity} onChange={(e) => setEquity(e.target.value)} /></Field>
          {!isClose && (
            <Field label="Term sheet link (optional)"><Input type="url" placeholder="https://" value={url} onChange={(e) => setUrl(e.target.value)} /></Field>
          )}
          <Button type="submit" className="w-full" disabled={action.isPending}>
            {action.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isClose ? "Close deal" : "Send term sheet"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function DealCard({ deal, side }: { deal: Deal; side: Side }) {
  const action = useDealAction(side)
  const [dialog, setDialog] = useState<"term_sheet" | "close" | null>(null)
  const isInvestor = side === "investor"
  const isOpen = OPEN_STAGES.includes(deal.status)
  const atTermSheet = deal.status === "term_sheet_sent"
  // The list response omits founder_accepted_at and the term sheet link.
  const { data: detail } = useDealDetail(deal.id, side, atTermSheet)
  const accepted = !!detail?.founder_accepted_at
  const next = NEXT_STAGE[deal.status]
  const investorName = `${deal.investor.first_name} ${deal.investor.last_name}`.trim() || deal.investor.email

  const run = (name: string, body: Record<string, unknown> | undefined, message: string) =>
    action.mutate({ id: deal.id, action: name, body }, { onSuccess: () => toast.success(message) })

  return (
    <Card className="shadow-sm" data-testid={`deal-${deal.id}`} data-startup={deal.startup.name}>
      <CardContent className="space-y-2 p-3">
        <div className="flex items-center gap-2">
          <Building2 className="h-4 w-4 shrink-0 text-muted-foreground" />
          <Link href={`/startup/${deal.startup.id}`} className="truncate text-sm font-medium hover:underline">{deal.startup.name}</Link>
        </div>
        {!isInvestor && (
          <p className="flex items-center gap-2 text-xs text-muted-foreground"><User className="h-3 w-3 shrink-0" /><span className="truncate">{investorName}</span></p>
        )}
        <div className="space-y-0.5 text-xs text-muted-foreground">
          {money(deal.amount_requested) && <p>Requested: {money(deal.amount_requested)}</p>}
          {money(deal.amount_offered) && <p>Offered: {money(deal.amount_offered)}{deal.equity_offered ? ` for ${Number(deal.equity_offered)}%` : ""}</p>}
        </div>

        {atTermSheet && (
          <p className="text-xs">
            {detail ? (accepted ? <span className="text-emerald-500">Founder accepted the term sheet</span> : <span className="text-amber-500">Awaiting founder acceptance</span>) : "Checking term sheet..."}
            {detail?.term_sheet_url && (
              <a href={detail.term_sheet_url} target="_blank" rel="noopener noreferrer" className="ml-1 inline-flex items-center gap-0.5 underline">
                link <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </p>
        )}

        {isOpen && (
          <div className="flex flex-col gap-1.5 border-t pt-2">
            {next && (
              <Button size="sm" variant="outline" className="justify-start" disabled={action.isPending}
                onClick={() => run("move_stage", { status: next }, `Moved to ${dealStageLabel(next)}`)}>
                <ArrowRight className="mr-1 h-3 w-3" /> Move to {dealStageLabel(next)}
              </Button>
            )}
            {isInvestor && deal.status === "negotiating" && (
              <Button size="sm" onClick={() => setDialog("term_sheet")}>Send term sheet</Button>
            )}
            {!isInvestor && deal.status === "negotiating" && (
              <p className="text-xs text-muted-foreground">Waiting for the investor to send a term sheet.</p>
            )}
            {isInvestor && atTermSheet && (
              <Button size="sm" disabled={!accepted} onClick={() => setDialog("close")}>Close deal</Button>
            )}
            {!isInvestor && atTermSheet && !accepted && (
              <Button size="sm" disabled={action.isPending} onClick={() => run("accept_term_sheet", undefined, "Term sheet accepted. The investor can now close.")}>
                <CheckCircle2 className="mr-1 h-3 w-3" /> Accept term sheet
              </Button>
            )}
            {atTermSheet && (
              <Button size="sm" variant="ghost" disabled={action.isPending}
                onClick={() => run("move_stage", { status: "negotiating" }, "Back to negotiating")}>
                Back to negotiating
              </Button>
            )}
            <Button size="sm" variant="ghost" className="justify-start text-destructive" disabled={action.isPending}
              onClick={() => {
                if (confirm(isInvestor ? "Withdraw from this deal?" : "Reject this deal?")) {
                  if (isInvestor) run("withdraw", {}, "Withdrawn from deal")
                  else run("reject", {}, "Deal rejected")
                }
              }}>
              <XCircle className="mr-1 h-3 w-3" /> {isInvestor ? "Withdraw" : "Reject"}
            </Button>
          </div>
        )}
      </CardContent>
      {dialog && <AmountDialog deal={deal} side={side} kind={dialog} onClose={() => setDialog(null)} />}
    </Card>
  )
}

export function DealBoard({ deals, side, isLoading }: { deals: Deal[] | undefined; side: Side; isLoading: boolean }) {
  const columns = [...DEAL_STAGES, { value: "closed_out", label: side === "investor" ? "Withdrawn / Rejected" : "Rejected / Withdrawn" }]

  if (isLoading) {
    return (
      <div className="flex gap-4 overflow-x-auto pb-4">
        {columns.map((c) => <Skeleton key={c.value} className="h-64 min-w-[240px] flex-1" />)}
      </div>
    )
  }

  return (
    <div className="flex gap-3 overflow-x-auto pb-4">
      {columns.map((col) => {
        const rows = (deals ?? []).filter((d) =>
          col.value === "closed_out" ? d.status === "rejected" || d.status === "withdrawn" : d.status === col.value,
        )
        return (
          <section key={col.value} aria-label={col.label} data-stage={col.value} className="min-w-[240px] flex-1 space-y-2 rounded-lg border bg-muted/30 p-2">
            <div className="flex items-center justify-between px-1">
              <h2 className="text-sm font-semibold">{col.label}</h2>
              <Badge variant="secondary">{rows.length}</Badge>
            </div>
            {rows.length === 0 ? (
              <p className="px-1 py-6 text-center text-xs text-muted-foreground">No deals</p>
            ) : (
              rows.map((deal) => <DealCard key={deal.id} deal={deal} side={side} />)
            )}
          </section>
        )
      })}
    </div>
  )
}
