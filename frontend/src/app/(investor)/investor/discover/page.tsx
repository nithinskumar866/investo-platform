"use client"

import { useState } from "react"
import { useStartups, useMatches } from "@/hooks/use-api"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { formatCurrency } from "@/lib/utils"
import { Search, MapPin, Filter, X } from "lucide-react"
import Link from "next/link"

const sectors = ["AI/ML", "Fintech", "HealthTech", "SaaS", "CleanTech", "EdTech", "BioTech", "PropTech"]
const stages = ["Pre-Seed", "Seed", "Series A", "Series B", "Series C+"]
const ticketSizes = ["Under $100k", "$100k–$500k", "$500k–$2M", "$2M+"]

export default function DiscoverPage() {
  const [search, setSearch] = useState("")
  const [selectedSectors, setSelectedSectors] = useState<string[]>([])
  const [selectedStages, setSelectedStages] = useState<string[]>([])
  const [selectedTickets, setSelectedTickets] = useState<string[]>([])
  const [showFilters, setShowFilters] = useState(false)

  const { data: startups, isLoading } = useStartups({ search, status: "verified" })
  const { data: matches } = useMatches("startup")

  const matchMap = new Map((matches ?? []).map((m) => [m.startup, m.score]))

  const filtered = (startups ?? []).filter((s) => {
    if (selectedSectors.length && !selectedSectors.includes(s.industry)) return false
    if (selectedStages.length && !selectedStages.includes(s.stage)) return false
    return true
  })

  function toggle(arr: string[], val: string) {
    return arr.includes(val) ? arr.filter((v) => v !== val) : [...arr, val]
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Discover Startups</h1>
        <p className="text-muted-foreground">Find and connect with high-potential startups</p>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search startups by name, industry, or location..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Button variant="outline" size="icon" onClick={() => setShowFilters(!showFilters)}>
          <Filter className="h-4 w-4" />
        </Button>
      </div>

      {showFilters && (
        <Card>
          <CardContent className="p-4 space-y-4">
            <div>
              <p className="text-sm font-medium mb-2">Sector</p>
              <div className="flex flex-wrap gap-2">
                {sectors.map((s) => (
                  <Badge
                    key={s}
                    variant={selectedSectors.includes(s) ? "default" : "outline"}
                    className="cursor-pointer"
                    onClick={() => setSelectedSectors(toggle(selectedSectors, s))}
                  >
                    {s}
                  </Badge>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sm font-medium mb-2">Stage</p>
              <div className="flex flex-wrap gap-2">
                {stages.map((s) => (
                  <Badge
                    key={s}
                    variant={selectedStages.includes(s) ? "default" : "outline"}
                    className="cursor-pointer"
                    onClick={() => setSelectedStages(toggle(selectedStages, s))}
                  >
                    {s}
                  </Badge>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sm font-medium mb-2">Ticket Size</p>
              <div className="flex flex-wrap gap-2">
                {ticketSizes.map((s) => (
                  <Badge
                    key={s}
                    variant={selectedTickets.includes(s) ? "default" : "outline"}
                    className="cursor-pointer"
                    onClick={() => setSelectedTickets(toggle(selectedTickets, s))}
                  >
                    {s}
                  </Badge>
                ))}
              </div>
            </div>
            {(selectedSectors.length > 0 || selectedStages.length > 0 || selectedTickets.length > 0) && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => { setSelectedSectors([]); setSelectedStages([]); setSelectedTickets([]) }}
              >
                <X className="mr-1 h-3 w-3" /> Clear all filters
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6 space-y-3">
                <Skeleton className="h-5 w-3/4" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-1/2" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center text-muted-foreground">
            No startups match your criteria.
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((s) => {
            const score = matchMap.get(s.id)
            return (
              <Link key={s.id} href={`/startup/${s.slug}`}>
                <Card className="h-full transition-colors hover:bg-accent/50 cursor-pointer">
                  <CardContent className="p-5 space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-semibold">{s.name}</h3>
                        <p className="text-sm text-muted-foreground line-clamp-2">{s.tagline}</p>
                      </div>
                      {score !== undefined && (
                        <Badge variant={score >= 80 ? "success" : score >= 50 ? "warning" : "secondary"} className="shrink-0">
                          {Math.round(score)}%
                        </Badge>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="secondary" className="text-xs">{s.industry}</Badge>
                      <Badge variant="outline" className="text-xs">{s.stage}</Badge>
                    </div>
                    {s.location && (
                      <p className="flex items-center gap-1 text-xs text-muted-foreground">
                        <MapPin className="h-3 w-3" /> {s.location}
                      </p>
                    )}
                    {s.valuation && (
                      <p className="text-sm text-muted-foreground">
                        Valuation: {formatCurrency(s.valuation)}
                      </p>
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
