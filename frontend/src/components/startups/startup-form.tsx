"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import { Loader2, Plus, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Field } from "@/components/ui/field"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useCreateStartup, usePublishStartup, useUpdateStartup } from "@/hooks/use-api"
import { BUSINESS_MODELS, INDUSTRIES, STAGES } from "@/lib/constants"
import type { StartupDetail, TeamMember } from "@/types/api"

const TEXT_FIELDS = ["name", "tagline", "short_description", "description", "industry", "stage", "business_model", "location", "website"] as const
const NUMBER_FIELDS = ["funding_goal", "equity_offered", "valuation", "team_size"] as const
const METRIC_FIELDS = ["monthly_revenue", "monthly_active_users", "burn_rate", "runway_months"] as const

type Values = Record<string, string>

function initialValues(startup?: StartupDetail): Values {
  const values: Values = {}
  for (const f of [...TEXT_FIELDS, ...NUMBER_FIELDS]) {
    const v = startup?.[f]
    values[f] = v === null || v === undefined ? "" : String(v)
  }
  for (const f of METRIC_FIELDS) {
    const v = startup?.metrics?.[f]
    values[f] = v === null || v === undefined ? "" : String(v)
  }
  return values
}

/** The form behind both /founder/startups/new and the edit page. */
export function StartupForm({ startup }: { startup?: StartupDetail }) {
  const router = useRouter()
  const create = useCreateStartup()
  const update = useUpdateStartup(startup?.id ?? 0)
  const publish = usePublishStartup()
  const [values, setValues] = useState<Values>(() => initialValues(startup))
  const [team, setTeam] = useState<TeamMember[]>(startup?.team_members?.map(({ name, role }) => ({ name, role })) ?? [])

  const set = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setValues((prev) => ({ ...prev, [e.target.name]: e.target.value }))

  const busy = create.isPending || update.isPending || publish.isPending
  const isDraft = !startup || startup.status === "draft"

  const buildPayload = () => {
    const payload: Record<string, unknown> = {}
    for (const f of TEXT_FIELDS) payload[f] = values[f].trim()
    // Blank numbers must be null: DRF rejects "" for decimal fields.
    for (const f of NUMBER_FIELDS) payload[f] = values[f] === "" ? null : values[f]
    payload.team_members = team.filter((m) => m.name.trim() && m.role.trim())
    const metrics = Object.fromEntries(METRIC_FIELDS.filter((f) => values[f] !== "").map((f) => [f, values[f]]))
    if (Object.keys(metrics).length) payload.metrics = metrics
    return payload
  }

  const save = async (andPublish: boolean) => {
    if (!values.name.trim() || !values.tagline.trim() || !values.industry || !values.stage) {
      toast.error("Name, tagline, industry and stage are required.")
      return
    }
    try {
      const saved = startup ? await update.mutateAsync(buildPayload()) : await create.mutateAsync(buildPayload())
      if (andPublish) await publish.mutateAsync(saved.id)
      toast.success(andPublish ? "Startup published. Investors can now find it." : "Startup saved.")
      router.push("/founder/startups")
    } catch {
      // The API message is already shown by the global mutation error toast.
    }
  }

  return (
    <form className="space-y-6" onSubmit={(e) => { e.preventDefault(); save(false) }}>
      <Card>
        <CardHeader>
          <CardTitle>Basic information</CardTitle>
          <CardDescription>A draft is only visible to you. Publishing shows it to investors.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Field label="Startup name *"><Input name="name" value={values.name} onChange={set} placeholder="e.g. Acme Corp" /></Field>
          <Field label="Tagline *"><Input name="tagline" value={values.tagline} onChange={set} placeholder="One line on what you do" /></Field>
          <Field label="Short description"><Input name="short_description" value={values.short_description} onChange={set} maxLength={500} /></Field>
          <Field label="Description"><Textarea name="description" value={values.description} onChange={set} /></Field>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Industry *"><Select name="industry" value={values.industry} onChange={set} placeholder="Select industry" options={INDUSTRIES} /></Field>
            <Field label="Stage *"><Select name="stage" value={values.stage} onChange={set} placeholder="Select stage" options={STAGES} /></Field>
            <Field label="Business model"><Select name="business_model" value={values.business_model} onChange={set} placeholder="Select model" options={BUSINESS_MODELS} /></Field>
            <Field label="Location"><Input name="location" value={values.location} onChange={set} placeholder="e.g. Bengaluru" /></Field>
          </div>
          <Field label="Website"><Input name="website" type="url" value={values.website} onChange={set} placeholder="https://" /></Field>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Funding</CardTitle>
          <CardDescription>All amounts on this platform are dummy money.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <Field label="Funding goal ($)"><Input name="funding_goal" type="number" min="0" value={values.funding_goal} onChange={set} /></Field>
          <Field label="Equity offered (%)"><Input name="equity_offered" type="number" min="0" max="100" step="0.01" value={values.equity_offered} onChange={set} /></Field>
          <Field label="Valuation ($)"><Input name="valuation" type="number" min="0" value={values.valuation} onChange={set} /></Field>
          <Field label="Team size"><Input name="team_size" type="number" min="0" value={values.team_size} onChange={set} /></Field>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Metrics</CardTitle>
          <CardDescription>Optional. Shown to signed-in investors on your startup page.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <Field label="Monthly revenue ($)"><Input name="monthly_revenue" type="number" min="0" value={values.monthly_revenue} onChange={set} /></Field>
          <Field label="Monthly active users"><Input name="monthly_active_users" type="number" min="0" value={values.monthly_active_users} onChange={set} /></Field>
          <Field label="Burn rate ($/month)"><Input name="burn_rate" type="number" min="0" value={values.burn_rate} onChange={set} /></Field>
          <Field label="Runway (months)"><Input name="runway_months" type="number" min="0" value={values.runway_months} onChange={set} /></Field>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Team</CardTitle>
          <Button type="button" variant="outline" size="sm" onClick={() => setTeam((t) => [...t, { name: "", role: "" }])}>
            <Plus className="mr-1 h-3 w-3" /> Add member
          </Button>
        </CardHeader>
        <CardContent className="space-y-3">
          {team.length === 0 && <p className="text-sm text-muted-foreground">No team members added.</p>}
          {team.map((m, i) => (
            <div key={i} className="flex items-center gap-2">
              <Input aria-label={`Team member ${i + 1} name`} placeholder="Name" value={m.name}
                onChange={(e) => setTeam((t) => t.map((x, j) => (j === i ? { ...x, name: e.target.value } : x)))} />
              <Input aria-label={`Team member ${i + 1} role`} placeholder="Role" value={m.role}
                onChange={(e) => setTeam((t) => t.map((x, j) => (j === i ? { ...x, role: e.target.value } : x)))} />
              <Button type="button" variant="ghost" size="icon" aria-label={`Remove team member ${i + 1}`}
                onClick={() => setTeam((t) => t.filter((_, j) => j !== i))}>
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </div>
          ))}
        </CardContent>
      </Card>

      <div className="flex flex-wrap justify-end gap-2">
        <Button type="button" variant="outline" onClick={() => router.push("/founder/startups")}>Cancel</Button>
        <Button type="submit" variant={isDraft ? "secondary" : "default"} disabled={busy}>
          {busy && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {startup ? "Save changes" : "Save as draft"}
        </Button>
        {isDraft && (
          <Button type="button" disabled={busy} onClick={() => save(true)}>
            Save and publish
          </Button>
        )}
      </div>
    </form>
  )
}
