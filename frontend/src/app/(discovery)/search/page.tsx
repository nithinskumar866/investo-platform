"use client"

import { useState } from "react"
import Link from "next/link"
import { useSearch } from "@/hooks/use-api"
import { useDebounce } from "@/hooks/use-debounce"
import { useAuthStore } from "@/stores/auth"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Field } from "@/components/ui/field"
import { Skeleton } from "@/components/ui/skeleton"
import { SearchIcon, Building2, Users, UserCheck, Briefcase, Filter } from "lucide-react"
import { INDUSTRIES, STAGES, dealStageLabel, humanize, industryLabel, stageLabel } from "@/lib/constants"
import { formatCurrency } from "@/lib/utils"

const tabs = [
  { key: "startups", label: "Startups", icon: Building2 },
  { key: "investors", label: "Investors", icon: Users },
  { key: "founders", label: "Founders", icon: UserCheck },
  { key: "opportunities", label: "Opportunities", icon: Briefcase },
]

function Result({ tab, item, role }: { tab: string; item: Record<string, any>; role?: string }) {
  if (tab === "startups") {
    return (
      <Link href={`/startup/${item.id}`}>
        <Card className="h-full transition-colors hover:bg-accent/10">
          <CardContent className="p-4">
            <h3 className="font-medium">{item.name}</h3>
            <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{item.tagline}</p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              <Badge variant="secondary">{industryLabel(item.industry)}</Badge>
              <Badge variant="outline">{stageLabel(item.stage)}</Badge>
            </div>
          </CardContent>
        </Card>
      </Link>
    )
  }
  if (tab === "opportunities") {
    return (
      <Card className="h-full">
        <CardContent className="p-4">
          <h3 className="font-medium">{item.startup_name}</h3>
          <p className="mt-1 text-sm text-muted-foreground">{item.investor_email}</p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            <Badge variant="secondary">{dealStageLabel(item.status)}</Badge>
            {item.amount_requested && <Badge variant="outline">{formatCurrency(item.amount_requested)}</Badge>}
          </div>
        </CardContent>
      </Card>
    )
  }
  const canMessage = (tab === "investors" && role === "entrepreneur") || (tab === "founders" && role === "investor")
  return (
    <Card className="h-full">
      <CardContent className="space-y-2 p-4">
        <h3 className="font-medium">{`${item.first_name} ${item.last_name}`.trim() || item.email}</h3>
        <p className="line-clamp-2 text-sm text-muted-foreground">{item.tagline || item.company_name || item.bio}</p>
        <div className="flex flex-wrap items-center gap-1.5">
          {item.investor_type && <Badge variant="secondary" className="capitalize">{humanize(item.investor_type)}</Badge>}
          {item.funding_stage && <Badge variant="outline">{stageLabel(item.funding_stage)}</Badge>}
          {canMessage && (
            <Button variant="outline" size="sm" asChild className="ml-auto">
              <Link href={`/chat?participant=${item.id}`}>Message</Link>
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export default function SearchPage() {
  const role = useAuthStore((s) => s.user?.role)
  const [activeTab, setActiveTab] = useState("startups")
  const [query, setQuery] = useState("")
  const [industry, setIndustry] = useState("")
  const [stage, setStage] = useState("")
  const [location, setLocation] = useState("")
  const debouncedQuery = useDebounce(query)
  const debouncedLocation = useDebounce(location)

  const params: Record<string, unknown> = { q: debouncedQuery || undefined }
  const isStartups = activeTab === "startups"
  if (isStartups) {
    params.industry = industry || undefined
    params.stage = stage || undefined
    params.location = debouncedLocation || undefined
  }
  const hasInput = !!debouncedQuery || (isStartups && !!(industry || stage || debouncedLocation))

  const { data, isLoading } = useSearch(activeTab, params, hasInput)
  const results = data?.results ?? []

  return (
    <div className="flex flex-col gap-6 lg:flex-row">
      {isStartups && (
        <aside className="w-full shrink-0 lg:w-64">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm"><Filter className="h-4 w-4" /> Filters</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Field label="Industry"><Select value={industry} onChange={(e) => setIndustry(e.target.value)} placeholder="All industries" options={INDUSTRIES} /></Field>
              <Field label="Stage"><Select value={stage} onChange={(e) => setStage(e.target.value)} placeholder="All stages" options={STAGES} /></Field>
              <Field label="Location"><Input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="e.g. Boston" /></Field>
            </CardContent>
          </Card>
        </aside>
      )}

      <div className="min-w-0 flex-1">
        <div className="relative mb-6">
          <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            aria-label="Search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search startups, investors, founders..."
            className="pl-9"
          />
        </div>

        <div className="mb-6 flex gap-1 overflow-x-auto border-b border-border" role="tablist">
          {tabs.map((tab) => {
            const active = activeTab === tab.key
            return (
              <button
                key={tab.key}
                type="button"
                role="tab"
                aria-selected={active}
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center gap-2 whitespace-nowrap border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
                  active ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                <tab.icon className="h-4 w-4" />
                {tab.label}
              </button>
            )
          })}
        </div>

        {hasInput && isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2">
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-28" />)}
          </div>
        ) : hasInput && results.length ? (
          <>
            <div className="grid gap-4 sm:grid-cols-2">
              {results.map((item) => <Result key={item.id} tab={activeTab} item={item} role={role} />)}
            </div>
            <p className="mt-4 text-center text-sm text-muted-foreground">{results.length} result{results.length !== 1 ? "s" : ""}</p>
          </>
        ) : (
          <div className="flex flex-col items-center gap-2 py-20 text-muted-foreground">
            <SearchIcon className="h-10 w-10" />
            <p className="text-sm">{hasInput ? "No results found" : "Enter a search term to get started"}</p>
          </div>
        )}
      </div>
    </div>
  )
}
