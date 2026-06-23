"use client"

import { useStartups } from "@/hooks/use-api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Plus, MapPin, Users, Eye, Globe } from "lucide-react"
import { formatDate, formatCurrency } from "@/lib/utils"

const statusVariant: Record<string, "success" | "warning" | "secondary" | "default" | "destructive" | "outline"> = {
  active: "success",
  pending: "warning",
  draft: "secondary",
  rejected: "destructive",
}

export default function StartupsPage() {
  const { data: startups, isLoading } = useStartups()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">My Startups</h1>
          <p className="text-muted-foreground">Manage your startup profiles</p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" /> New Startup
        </Button>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader><Skeleton className="h-5 w-32" /></CardHeader>
              <CardContent className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {startups?.map((startup) => (
            <Card key={startup.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="flex flex-row items-start justify-between">
                <div>
                  <CardTitle>{startup.name}</CardTitle>
                  <p className="text-sm text-muted-foreground mt-1">{startup.tagline}</p>
                </div>
                <Badge variant={statusVariant[startup.status] ?? "outline"}>{startup.status}</Badge>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <MapPin className="h-3.5 w-3.5" />
                    <span>{startup.location || "N/A"}</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Users className="h-3.5 w-3.5" />
                    <span>{startup.team_size ?? "—"} team members</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Eye className="h-3.5 w-3.5" />
                    <span>{startup.view_count} views</span>
                  </div>
                  {startup.industry && (
                    <Badge variant="outline">{startup.industry}</Badge>
                  )}
                  <div className="pt-2 border-t flex items-center justify-between">
                    <span className="font-medium">{startup.funding_goal ? formatCurrency(startup.funding_goal) : "—"}</span>
                    <span className="text-xs text-muted-foreground">Stage: {startup.stage}</span>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Globe className="h-3 w-3" />
                    <span>Created {formatDate(startup.created_at)}</span>
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
