"use client"

import Link from "next/link"
import { toast } from "sonner"
import { useDeleteStartup, useMyStartups, usePublishStartup } from "@/hooks/use-api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Building2, Eye, MapPin, Pencil, Plus, Rocket, Trash2, Users } from "lucide-react"
import { formatCurrency } from "@/lib/utils"
import { industryLabel, stageLabel } from "@/lib/constants"

const statusVariant: Record<string, "success" | "warning" | "secondary" | "default" | "outline"> = {
  active: "success",
  funded: "default",
  draft: "secondary",
  closed: "outline",
}

export default function StartupsPage() {
  const { data: startups, isLoading } = useMyStartups()
  const publish = usePublishStartup()
  const remove = useDeleteStartup()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">My Startups</h1>
          <p className="text-muted-foreground">Manage your startup profiles</p>
        </div>
        <Button asChild>
          <Link href="/founder/startups/new">
            <Plus className="mr-2 h-4 w-4" /> New Startup
          </Link>
        </Button>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-56" />)}
        </div>
      ) : !startups?.length ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-16 text-center">
            <Building2 className="h-10 w-10 text-muted-foreground" />
            <p className="font-medium">You have no startups yet</p>
            <p className="text-sm text-muted-foreground">Create one to start matching with investors.</p>
            <Button asChild><Link href="/founder/startups/new">Create your first startup</Link></Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {startups.map((startup) => (
            <Card key={startup.id} data-testid={`startup-card-${startup.id}`}>
              <CardHeader className="flex flex-row items-start justify-between gap-2">
                <div className="min-w-0">
                  <CardTitle><Link href={`/startup/${startup.id}`} className="hover:underline">{startup.name}</Link></CardTitle>
                  <p className="mt-1 text-sm text-muted-foreground">{startup.tagline}</p>
                </div>
                <Badge variant={statusVariant[startup.status] ?? "outline"}>{startup.status}</Badge>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-2 text-sm text-muted-foreground">
                  <div className="flex items-center gap-2"><MapPin className="h-3.5 w-3.5" /><span>{startup.location || "No location set"}</span></div>
                  <div className="flex items-center gap-2"><Users className="h-3.5 w-3.5" /><span>{startup.team_size ?? "Unknown"} team members</span></div>
                  <div className="flex items-center gap-2"><Eye className="h-3.5 w-3.5" /><span>{startup.view_count} views</span></div>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  <Badge variant="outline">{industryLabel(startup.industry)}</Badge>
                  <Badge variant="secondary">{stageLabel(startup.stage)}</Badge>
                </div>
                <p className="text-sm font-medium">{startup.funding_goal ? `Goal: ${formatCurrency(startup.funding_goal)}` : "No funding goal set"}</p>
                <div className="flex flex-wrap gap-2 border-t pt-3">
                  {startup.status === "draft" && (
                    <Button size="sm" disabled={publish.isPending}
                      onClick={() => publish.mutate(startup.id, { onSuccess: () => toast.success(`${startup.name} is now published`) })}>
                      <Rocket className="mr-1 h-3 w-3" /> Publish
                    </Button>
                  )}
                  <Button size="sm" variant="outline" asChild>
                    <Link href={`/founder/startups/${startup.id}/edit`}><Pencil className="mr-1 h-3 w-3" /> Edit</Link>
                  </Button>
                  <Button size="sm" variant="ghost" className="text-destructive" disabled={remove.isPending}
                    onClick={() => {
                      if (confirm(`Delete ${startup.name}? This cannot be undone.`)) {
                        remove.mutate(startup.id, { onSuccess: () => toast.success("Startup deleted") })
                      }
                    }}>
                    <Trash2 className="mr-1 h-3 w-3" /> Delete
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
