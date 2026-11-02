"use client"

import { useState } from "react"
import Link from "next/link"
import { useMatches, useStartups } from "@/hooks/use-api"
import { useDebounce } from "@/hooks/use-debounce"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { formatCurrency } from "@/lib/utils"
import { INDUSTRIES, STAGES, industryLabel, stageLabel } from "@/lib/constants"
import { Search, MapPin, X } from "lucide-react"

export default function DiscoverPage() {
  const [search, setSearch] = useState("")
  const [industry, setIndustry] = useState("")
  const [stage, setStage] = useState("")
  const debouncedSearch = useDebounce(search)

  // Without a status filter the API returns only published (active and funded) startups.
  const { data: startups, isLoading } = useStartups({
    search: debouncedSearch || undefined,
    industry: industry || undefined,
    stage: stage || undefined,
    per_page: 100,
  })
  const { data: matches } = useMatches("startup")
  const matchMap = new Map((matches ?? []).map((m) => [m.startup_id, m.score]))
  const hasFilters = !!(search || industry || stage)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Discover Startups</h1>
        <p className="text-muted-foreground">Find and connect with high-potential startups</p>
      </div>

      <div className="flex flex-col gap-3 md:flex-row md:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            aria-label="Search startups"
            placeholder="Search startups by name, description, or location..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Select aria-label="Filter by industry" className="md:w-56" value={industry} onChange={(e) => setIndustry(e.target.value)} placeholder="All industries" options={INDUSTRIES} />
        <Select aria-label="Filter by stage" className="md:w-44" value={stage} onChange={(e) => setStage(e.target.value)} placeholder="All stages" options={STAGES} />
        {hasFilters && (
          <Button variant="ghost" size="sm" onClick={() => { setSearch(""); setIndustry(""); setStage("") }}>
            <X className="mr-1 h-3 w-3" /> Clear
          </Button>
        )}
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-44" />)}
        </div>
      ) : !startups?.length ? (
        <Card>
          <CardContent className="p-12 text-center text-muted-foreground">
            {hasFilters ? "No startups match your search." : "No startups have been published yet."}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {startups.map((s) => {
            const score = matchMap.get(s.id)
            return (
              <Link key={s.id} href={`/startup/${s.id}`} data-testid={`startup-link-${s.id}`}>
                <Card className="h-full cursor-pointer transition-colors hover:bg-accent/10">
                  <CardContent className="space-y-3 p-5">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <h3 className="font-semibold">{s.name}</h3>
                        <p className="line-clamp-2 text-sm text-muted-foreground">{s.tagline}</p>
                      </div>
                      {score !== undefined && (
                        <Badge variant={score >= 80 ? "success" : score >= 50 ? "warning" : "secondary"} className="shrink-0">
                          {Math.round(score)}%
                        </Badge>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="secondary" className="text-xs">{industryLabel(s.industry)}</Badge>
                      <Badge variant="outline" className="text-xs">{stageLabel(s.stage)}</Badge>
                      {s.status === "funded" && <Badge variant="success" className="text-xs">Funded</Badge>}
                    </div>
                    {s.location && (
                      <p className="flex items-center gap-1 text-xs text-muted-foreground">
                        <MapPin className="h-3 w-3" /> {s.location}
                      </p>
                    )}
                    {s.funding_goal && (
                      <p className="text-sm text-muted-foreground">Goal: {formatCurrency(s.funding_goal)}</p>
                    )}
                  </CardContent>
                </Card>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}
