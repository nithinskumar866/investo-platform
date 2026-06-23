"use client"

import { useState } from "react"
import {
  Card, CardHeader, CardTitle, CardDescription, CardContent,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { useStartups } from "@/hooks/use-api"
import { formatCurrency } from "@/lib/utils"
import { Search, CheckCircle, XCircle, ExternalLink } from "lucide-react"

export default function AdminStartupsPage() {
  const [search, setSearch] = useState("")
  const [filter, setFilter] = useState<string>("all")
  const { data: startups, isLoading } = useStartups({ search, status: filter !== "all" ? filter : undefined })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Startup Moderation</h1>
        <p className="text-muted-foreground">Review and approve startup listings</p>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search startups..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          {["all", "pending", "approved", "rejected"].map((s) => (
            <Button
              key={s}
              variant={filter === s ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter(s)}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </Button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      ) : (
        <Card>
          <div className="divide-y">
            {(startups as Array<{
              id: number; name: string; slug: string; tagline: string;
              industry: string; stage: string; status: string; funding_goal: number | null;
              owner: number; created_at: string
            }>)?.map((startup) => (
              <div key={startup.id} className="flex items-center justify-between p-4">
                <div>
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium">{startup.name}</p>
                    <Badge variant="outline">{startup.industry}</Badge>
                    <Badge variant="secondary">{startup.stage}</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{startup.tagline}</p>
                  <p className="text-xs text-muted-foreground">
                    {startup.funding_goal ? `Goal: ${formatCurrency(startup.funding_goal)}` : ""} &middot; Owner #{startup.owner}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge
                    variant={
                      startup.status === "approved" ? "success"
                      : startup.status === "rejected" ? "destructive"
                      : "warning"
                    }
                  >
                    {startup.status}
                  </Badge>
                  <Button variant="ghost" size="icon" title="Approve">
                    <CheckCircle className="h-4 w-4 text-emerald-500" />
                  </Button>
                  <Button variant="ghost" size="icon" title="Reject">
                    <XCircle className="h-4 w-4 text-destructive" />
                  </Button>
                  <Button variant="ghost" size="icon" asChild>
                    <a href={`/startups/${startup.slug}`} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="h-4 w-4" />
                    </a>
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
