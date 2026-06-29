"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar } from "@/components/ui/avatar"
import { Input } from "@/components/ui/input"
import { Search, Filter, MapPin, Briefcase, DollarSign, MessageSquare, UserPlus } from "lucide-react"
import { useInvestors } from "@/hooks/use-api"
import { Skeleton } from "@/components/ui/skeleton"

const sectors = ["Fintech", "HealthTech", "AI/ML", "SaaS", "CleanTech", "EdTech", "BioTech", "E-Commerce", "PropTech", "Cyber Security"]

export default function DiscoverPage() {
  const [search, setSearch] = useState("")
  const [selectedSectors, setSelectedSectors] = useState<string[]>([])
  
  const { data: investors, isLoading, error } = useInvestors({
    search: search || undefined,
    industry: selectedSectors.length > 0 ? selectedSectors.join(",") : undefined,
  })

  const toggleSector = (sector: string) => {
    setSelectedSectors((prev) =>
      prev.includes(sector) ? prev.filter((s) => s !== sector) : [...prev, sector]
    )
  }

  // Formatting ticket sizes nicely
  const formatTicketSize = (min?: number, max?: number) => {
    if (!min && !max) return "Undisclosed"
    const fMin = min ? `$${(min / 1000).toFixed(0)}K` : "$0"
    const fMax = max ? `$${(max / 1000000).toFixed(1)}M` : "No limit"
    return `${fMin} – ${fMax}`
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Discover Investors</h1>
        <p className="text-muted-foreground">Find and connect with potential investors</p>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search investors or firms..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Button variant="outline" className="gap-2">
          <Filter className="h-4 w-4" /> Filters
        </Button>
      </div>

      <div className="flex flex-wrap gap-2">
        {sectors.map((sector) => (
          <Badge
            key={sector}
            variant={selectedSectors.includes(sector) ? "default" : "outline"}
            className="cursor-pointer"
            onClick={() => toggleSector(sector)}
          >
            {sector}
          </Badge>
        ))}
      </div>

      {error ? (
        <div className="text-center py-10 text-destructive">Failed to load investors.</div>
      ) : isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i} className="hover:shadow-md transition-shadow">
              <CardHeader className="flex flex-row items-start gap-4">
                <Skeleton className="h-12 w-12 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-1/2" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-4/5" />
                  <Skeleton className="h-3 w-2/3" />
                  <div className="flex gap-2 pt-3">
                    <Skeleton className="h-8 flex-1" />
                    <Skeleton className="h-8 flex-1" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : investors?.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground bg-muted/20 rounded-lg border border-dashed">
          <h3 className="text-lg font-semibold text-foreground">No investors found</h3>
          <p className="mt-1">Try adjusting your search or filters.</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {investors?.map((investor: any) => (
            <Card key={investor.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="flex flex-row items-start gap-4">
                <Avatar fallback={investor.user?.first_name?.[0] || "?"} className="h-12 w-12" />
                <div className="flex-1 min-w-0">
                  <CardTitle className="text-base">{investor.user?.first_name} {investor.user?.last_name}</CardTitle>
                  <p className="text-sm text-muted-foreground">{investor.tagline || investor.investor_type}</p>
                </div>
                {investor.lead_investor && (
                  <Badge variant="success" className="shrink-0">
                    Lead
                  </Badge>
                )}
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <MapPin className="h-3.5 w-3.5" />
                    <span>{investor.city || "Global"} {investor.country && `, ${investor.country}`}</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Briefcase className="h-3.5 w-3.5" />
                    <span>{investor.years_of_experience || 0} yrs experience</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <DollarSign className="h-3.5 w-3.5" />
                    <span>Check: {formatTicketSize(investor.ticket_size_min, investor.ticket_size_max)}</span>
                  </div>
                  <div className="flex flex-wrap gap-1 pt-1">
                    {(investor.preferred_industries || []).map((s: string) => (
                      <Badge key={s} variant="secondary" className="text-[10px]">{s}</Badge>
                    ))}
                  </div>
                  <div className="flex gap-2 pt-3">
                    <Button size="sm" className="flex-1 gap-1"><MessageSquare className="h-3.5 w-3.5" /> Message</Button>
                    <Button size="sm" variant="outline" className="flex-1 gap-1"><UserPlus className="h-3.5 w-3.5" /> Connect</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
