"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar } from "@/components/ui/avatar"
import { Input } from "@/components/ui/input"
import { Search, Filter, MapPin, Briefcase, DollarSign, MessageSquare, UserPlus } from "lucide-react"

const sectors = ["Fintech", "HealthTech", "AI/ML", "SaaS", "CleanTech", "EdTech", "BioTech", "E-Commerce", "PropTech", "Cyber Security"]
const checkRanges = [
  { label: "< $100K", min: 0, max: 100000 },
  { label: "$100K–$500K", min: 100000, max: 500000 },
  { label: "$500K–$1M", min: 500000, max: 1000000 },
  { label: "$1M–$5M", min: 1000000, max: 5000000 },
  { label: "$5M+", min: 5000000, max: null },
]

const mockInvestors = [
  { id: 1, name: "Sarah Chen", firm: "Velocity Ventures", location: "San Francisco, CA", sectors: ["Fintech", "AI/ML"], checkRange: "$500K–$2M", portfolioCount: 24, matchScore: 92 },
  { id: 2, name: "Marcus Johnson", firm: "Apex Capital", location: "New York, NY", sectors: ["SaaS", "HealthTech"], checkRange: "$1M–$5M", portfolioCount: 18, matchScore: 87 },
  { id: 3, name: "Priya Patel", firm: "Nexus Fund", location: "Austin, TX", sectors: ["AI/ML", "CleanTech"], checkRange: "$500K–$2M", portfolioCount: 31, matchScore: 85 },
  { id: 4, name: "Alex Rivera", firm: "Horizon Partners", location: "Boston, MA", sectors: ["BioTech", "HealthTech"], checkRange: "$2M–$10M", portfolioCount: 15, matchScore: 78 },
  { id: 5, name: "Emily Watson", firm: "Summit Equity", location: "Seattle, WA", sectors: ["SaaS", "EdTech"], checkRange: "$100K–$500K", portfolioCount: 42, matchScore: 73 },
  { id: 6, name: "David Kim", firm: "Pioneer Ventures", location: "Los Angeles, CA", sectors: ["E-Commerce", "PropTech"], checkRange: "$500K–$2M", portfolioCount: 27, matchScore: 71 },
]

export default function DiscoverPage() {
  const [search, setSearch] = useState("")
  const [selectedSectors, setSelectedSectors] = useState<string[]>([])

  const toggleSector = (sector: string) => {
    setSelectedSectors((prev) =>
      prev.includes(sector) ? prev.filter((s) => s !== sector) : [...prev, sector]
    )
  }

  const filtered = mockInvestors.filter(
    (inv) =>
      (!search || inv.name.toLowerCase().includes(search.toLowerCase()) || inv.firm.toLowerCase().includes(search.toLowerCase())) &&
      (!selectedSectors.length || selectedSectors.some((s) => inv.sectors.includes(s)))
  )

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

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filtered.map((investor) => (
          <Card key={investor.id} className="hover:shadow-md transition-shadow">
            <CardHeader className="flex flex-row items-start gap-4">
              <Avatar fallback={investor.name.split(" ").map((n) => n[0]).join("")} className="h-12 w-12" />
              <div className="flex-1 min-w-0">
                <CardTitle className="text-base">{investor.name}</CardTitle>
                <p className="text-sm text-muted-foreground">{investor.firm}</p>
              </div>
              <Badge variant={investor.matchScore >= 80 ? "success" : "warning"} className="shrink-0">
                {investor.matchScore}% match
              </Badge>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <MapPin className="h-3.5 w-3.5" />
                  <span>{investor.location}</span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Briefcase className="h-3.5 w-3.5" />
                  <span>{investor.portfolioCount} portfolio companies</span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <DollarSign className="h-3.5 w-3.5" />
                  <span>Check: {investor.checkRange}</span>
                </div>
                <div className="flex flex-wrap gap-1 pt-1">
                  {investor.sectors.map((s) => (
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
    </div>
  )
}
