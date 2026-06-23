"use client"

import { useState } from "react"
import { useSearch } from "@/hooks/use-api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { SearchIcon, Building2, Users, UserCheck, Briefcase, Filter, X } from "lucide-react"

const tabs = [
  { key: "startups", label: "Startups", icon: Building2 },
  { key: "investors", label: "Investors", icon: Users },
  { key: "founders", label: "Founders", icon: UserCheck },
  { key: "opportunities", label: "Opportunities", icon: Briefcase },
]

const industries = ["Tech", "Fintech", "Health", "AI", "SaaS", "Biotech", "CleanTech", "EdTech"]
const stages = ["Idea", "Pre-seed", "Seed", "Series A", "Series B", "Growth"]
const locations = ["US", "Europe", "Asia", "Africa", "LATAM", "Middle East"]

function ResultSkeleton() {
  return (
    <Card>
      <CardContent className="p-4">
        <Skeleton className="mb-2 h-5 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
      </CardContent>
    </Card>
  )
}

export default function SearchPage() {
  const [activeTab, setActiveTab] = useState("startups")
  const [query, setQuery] = useState("")
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedIndustries, setSelectedIndustries] = useState<string[]>([])
  const [selectedStages, setSelectedStages] = useState<string[]>([])
  const [selectedLocations, setSelectedLocations] = useState<string[]>()

  const params: Record<string, unknown> = { search: searchQuery || undefined }
  if (selectedIndustries.length) params.industry = selectedIndustries
  if (selectedStages.length) params.stage = selectedStages
  if (selectedLocations?.length) params.location = selectedLocations

  const { data, isLoading, refetch } = useSearch(activeTab, params)

  const handleSearch = () => {
    setSearchQuery(query)
    if (query || selectedIndustries.length || selectedStages.length) refetch()
  }

  const toggleFilter = (arr: string[], val: string, setter: (v: string[]) => void) => {
    setter(arr.includes(val) ? arr.filter((x) => x !== val) : [...arr, val])
  }

  return (
    <div className="flex gap-6">
      <aside className="hidden w-64 shrink-0 lg:block">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Filter className="h-4 w-4" /> Filters
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <div>
              <p className="mb-2 text-xs font-semibold text-muted-foreground uppercase">Industry</p>
              <div className="flex flex-wrap gap-1.5">
                {industries.map((ind) => (
                  <Badge
                    key={ind}
                    variant={selectedIndustries.includes(ind) ? "default" : "outline"}
                    className="cursor-pointer"
                    onClick={() => toggleFilter(selectedIndustries, ind, setSelectedIndustries)}
                  >
                    {ind}
                  </Badge>
                ))}
              </div>
            </div>
            <div>
              <p className="mb-2 text-xs font-semibold text-muted-foreground uppercase">Stage</p>
              <div className="flex flex-wrap gap-1.5">
                {stages.map((s) => (
                  <Badge
                    key={s}
                    variant={selectedStages.includes(s) ? "default" : "outline"}
                    className="cursor-pointer"
                    onClick={() => toggleFilter(selectedStages, s, setSelectedStages)}
                  >
                    {s}
                  </Badge>
                ))}
              </div>
            </div>
            <div>
              <p className="mb-2 text-xs font-semibold text-muted-foreground uppercase">Location</p>
              <div className="flex flex-wrap gap-1.5">
                {locations.map((l) => (
                  <Badge
                    key={l}
                    variant={selectedLocations?.includes(l) ? "default" : "outline"}
                    className="cursor-pointer"
                    onClick={() => {
                      if (selectedLocations?.includes(l)) {
                        setSelectedLocations(selectedLocations.filter((x) => x !== l))
                      } else {
                        setSelectedLocations([...(selectedLocations || []), l])
                      }
                    }}
                  >
                    {l}
                  </Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </aside>

      <div className="flex-1 min-w-0">
        <div className="mb-6 flex gap-2">
          <div className="relative flex-1">
            <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="Search startups, investors, founders..."
              className="pl-9"
            />
          </div>
          <Button onClick={handleSearch}>Search</Button>
        </div>

        <div className="mb-6 flex gap-1 border-b border-border">
          {tabs.map((tab) => {
            const active = activeTab === tab.key
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                  active ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                <tab.icon className="h-4 w-4" />
                {tab.label}
              </button>
            )
          })}
        </div>

        {isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2">
            {Array.from({ length: 4 }).map((_, i) => <ResultSkeleton key={i} />)}
          </div>
        ) : data?.results?.length ? (
          <div className="grid gap-4 sm:grid-cols-2">
            {data.results.map((item: Record<string, unknown>, i: number) => (
              <Card key={i} className="transition-colors hover:bg-accent/50">
                <CardContent className="p-4">
                  <h3 className="font-medium">{item.name as string || item.title as string}</h3>
                  <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
                    {item.tagline as string || item.description as string}
                  </p>
                  <div className="mt-2 flex gap-1.5">
                    {(item as { industry?: string }).industry && (
                      <Badge variant="secondary">{(item as { industry: string }).industry}</Badge>
                    )}
                    {(item as { stage?: string }).stage && (
                      <Badge variant="outline">{(item as { stage: string }).stage}</Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 py-20 text-muted-foreground">
            <SearchIcon className="h-10 w-10" />
            <p className="text-sm">{searchQuery ? "No results found" : "Enter a search term to get started"}</p>
          </div>
        )}

        {data && (
          <p className="mt-4 text-center text-sm text-muted-foreground">
            {data.count} result{data.count !== 1 ? "s" : ""} found
          </p>
        )}
      </div>
    </div>
  )
}
