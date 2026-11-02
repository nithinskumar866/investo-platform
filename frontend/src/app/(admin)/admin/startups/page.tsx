"use client"

import { useState } from "react"
import Link from "next/link"
import { toast } from "sonner"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { useAdminStartupAction, useAdminStartups } from "@/hooks/use-api"
import { industryLabel, stageLabel } from "@/lib/constants"
import { Search, CheckCircle, XCircle, Archive, Flag, BadgeCheck, ExternalLink } from "lucide-react"

const statusVariant: Record<string, "success" | "secondary" | "default" | "outline"> = {
  active: "success",
  funded: "default",
  draft: "secondary",
  closed: "outline",
}

export default function AdminStartupsPage() {
  const [search, setSearch] = useState("")
  const [filter, setFilter] = useState("all")
  const { data: startups, isLoading } = useAdminStartups({ status: filter !== "all" ? filter : undefined })
  const action = useAdminStartupAction()

  // The moderation endpoint has no text search, so this filters the loaded list.
  const rows = (startups ?? []).filter((s) => s.name.toLowerCase().includes(search.toLowerCase()) || s.owner_email.toLowerCase().includes(search.toLowerCase()))

  const run = (id: number, name: string, act: "approve" | "reject" | "archive" | "flag" | "verify", done: string) =>
    action.mutate({ id, action: act }, { onSuccess: () => toast.success(`${name} ${done}`) })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Startup Moderation</h1>
        <p className="text-muted-foreground">Approve moves a startup to active, reject back to draft, archive to closed. Flag removes its verified badge.</p>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative max-w-sm flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input aria-label="Search startups" placeholder="Search by name or owner..." className="pl-9" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <div className="flex flex-wrap gap-2">
          {["all", "draft", "active", "funded", "closed"].map((s) => (
            <Button key={s} variant={filter === s ? "default" : "outline"} size="sm" onClick={() => setFilter(s)}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </Button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-20 w-full" />)}
        </div>
      ) : rows.length === 0 ? (
        <Card><CardContent className="py-12 text-center text-sm text-muted-foreground">No startups match these filters.</CardContent></Card>
      ) : (
        <Card>
          <div className="divide-y">
            {rows.map((startup) => (
              <div key={startup.id} className="flex flex-wrap items-center justify-between gap-3 p-4">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <Link href={`/startup/${startup.id}`} className="text-sm font-medium hover:underline">{startup.name}</Link>
                    <Badge variant="outline">{industryLabel(startup.industry)}</Badge>
                    <Badge variant="secondary">{stageLabel(startup.stage)}</Badge>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">Owner: {startup.owner_email}</p>
                </div>
                <div className="flex flex-wrap items-center gap-1">
                  <Badge variant={statusVariant[startup.status] ?? "outline"}>{startup.status}</Badge>
                  {startup.is_verified && <Badge variant="success">Verified</Badge>}
                  {startup.status === "draft" && (
                    <Button variant="ghost" size="sm" disabled={action.isPending} onClick={() => run(startup.id, startup.name, "approve", "approved")}>
                      <CheckCircle className="mr-1 h-4 w-4 text-emerald-500" /> Approve
                    </Button>
                  )}
                  {startup.status === "active" && (
                    <Button variant="ghost" size="sm" disabled={action.isPending} onClick={() => run(startup.id, startup.name, "reject", "moved back to draft")}>
                      <XCircle className="mr-1 h-4 w-4 text-destructive" /> Reject
                    </Button>
                  )}
                  {startup.status !== "closed" && (
                    <Button variant="ghost" size="sm" disabled={action.isPending} onClick={() => run(startup.id, startup.name, "archive", "archived")}>
                      <Archive className="mr-1 h-4 w-4" /> Archive
                    </Button>
                  )}
                  {startup.is_verified ? (
                    <Button variant="ghost" size="sm" disabled={action.isPending} onClick={() => run(startup.id, startup.name, "flag", "flagged")}>
                      <Flag className="mr-1 h-4 w-4 text-amber-500" /> Flag
                    </Button>
                  ) : (
                    <Button variant="ghost" size="sm" disabled={action.isPending} onClick={() => run(startup.id, startup.name, "verify", "verified")}>
                      <BadgeCheck className="mr-1 h-4 w-4 text-emerald-500" /> Verify
                    </Button>
                  )}
                  <Button variant="ghost" size="icon" asChild>
                    <Link href={`/startup/${startup.id}`} aria-label={`Open ${startup.name}`}><ExternalLink className="h-4 w-4" /></Link>
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
