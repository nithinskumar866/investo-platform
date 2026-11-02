"use client"

import { useState } from "react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar } from "@/components/ui/avatar"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { MeetingDialog } from "@/components/meetings/meeting-dialog"
import { Search, MapPin, Briefcase, DollarSign, MessageSquare, Calendar } from "lucide-react"
import { useInvestors } from "@/hooks/use-api"
import { useDebounce } from "@/hooks/use-debounce"
import { INDUSTRIES, humanize, industryLabel } from "@/lib/constants"
import { formatCurrency, getInitials } from "@/lib/utils"

export default function DiscoverPage() {
  const [search, setSearch] = useState("")
  const [industry, setIndustry] = useState("")
  const [meetingInvestor, setMeetingInvestor] = useState<number | null>(null)
  const debouncedSearch = useDebounce(search)

  const { data: investors, isLoading, error } = useInvestors({
    search: debouncedSearch || undefined,
    industry: industry || undefined,
  })

  const ticket = (min?: string | null, max?: string | null) =>
    min || max ? `${min ? formatCurrency(min) : "Any"} to ${max ? formatCurrency(max) : "any"}` : "Undisclosed"

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Discover Investors</h1>
        <p className="text-muted-foreground">Find and connect with potential investors</p>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input aria-label="Search investors" placeholder="Search investors or firms..." className="pl-9" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <Select aria-label="Filter by industry" className="sm:w-60" value={industry} onChange={(e) => setIndustry(e.target.value)} placeholder="All industries" options={INDUSTRIES} />
      </div>

      {error ? (
        <div className="py-10 text-center text-destructive">Failed to load investors.</div>
      ) : isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => <Skeleton key={i} className="h-56" />)}
        </div>
      ) : investors?.length === 0 ? (
        <div className="rounded-lg border border-dashed bg-muted/20 py-16 text-center text-muted-foreground">
          <h3 className="text-lg font-semibold text-foreground">No investors found</h3>
          <p className="mt-1">Try adjusting your search or filters.</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {investors?.map((investor: any) => {
            const name = `${investor.user?.first_name ?? ""} ${investor.user?.last_name ?? ""}`.trim()
            return (
              <Card key={investor.id}>
                <CardHeader className="flex flex-row items-start gap-4">
                  <Avatar fallback={getInitials(name) || "?"} className="h-12 w-12" />
                  <div className="min-w-0 flex-1">
                    <CardTitle className="text-base">{name}</CardTitle>
                    <p className="text-sm text-muted-foreground">{investor.tagline || humanize(investor.investor_type)}</p>
                  </div>
                  {investor.lead_investor && <Badge variant="success" className="shrink-0">Lead</Badge>}
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm text-muted-foreground">
                    <div className="flex items-center gap-2"><MapPin className="h-3.5 w-3.5" /><span>{[investor.city, investor.country].filter(Boolean).join(", ") || "Location not set"}</span></div>
                    <div className="flex items-center gap-2"><Briefcase className="h-3.5 w-3.5" /><span>{investor.years_of_experience ?? 0} yrs experience</span></div>
                    <div className="flex items-center gap-2"><DollarSign className="h-3.5 w-3.5" /><span>Check: {ticket(investor.ticket_size_min, investor.ticket_size_max)}</span></div>
                    <div className="flex flex-wrap gap-1 pt-1">
                      {(investor.preferred_industries || []).map((s: string) => (
                        <Badge key={s} variant="secondary" className="text-[10px]">{industryLabel(s)}</Badge>
                      ))}
                    </div>
                    <div className="flex gap-2 pt-3">
                      <Button size="sm" className="flex-1 gap-1" asChild>
                        <Link href={`/chat?participant=${investor.user?.id}`}><MessageSquare className="h-3.5 w-3.5" /> Message</Link>
                      </Button>
                      <Button size="sm" variant="outline" className="flex-1 gap-1" onClick={() => setMeetingInvestor(investor.user?.id)}>
                        <Calendar className="h-3.5 w-3.5" /> Connect
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
      <MeetingDialog open={meetingInvestor !== null} onOpenChange={() => setMeetingInvestor(null)} investorId={meetingInvestor ?? undefined} />
    </div>
  )
}
