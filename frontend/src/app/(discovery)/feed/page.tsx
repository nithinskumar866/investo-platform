"use client"

import { useFeed } from "@/hooks/use-api"
import { formatRelativeTime } from "@/lib/utils"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Activity, Building2, UserPlus, Handshake, DollarSign, MessageSquare,
  Calendar, TrendingUp, Star, FileText, Target, Zap,
} from "lucide-react"

const activityIcons: Record<string, React.ElementType> = {
  startup_created: Building2, match_made: Handshake, investment: DollarSign,
  message: MessageSquare, meeting: Calendar, milestone: TrendingUp,
  review: Star, document: FileText, pitch: Target, connection: Zap,
}

function FeedItemSkeleton() {
  return (
    <Card className="mb-4">
      <CardContent className="flex items-start gap-4 p-4">
        <Skeleton className="h-10 w-10 rounded-full" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/3" />
        </div>
      </CardContent>
    </Card>
  )
}

function getInitialActivityIcon(type: string) {
  const Icon = activityIcons[type] || Activity
  return <Icon className="h-5 w-5" />
}

export default function FeedPage() {
  const { data: activities, isLoading } = useFeed()

  if (isLoading) {
    return (
      <div className="mx-auto max-w-2xl">
        <h1 className="mb-6 text-2xl font-bold">Activity Feed</h1>
        {Array.from({ length: 6 }).map((_, i) => <FeedItemSkeleton key={i} />)}
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-2xl">
      <Card className="mb-6">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary" />
            Activity Feed
          </CardTitle>
        </CardHeader>
      </Card>

      <div className="space-y-3">
        {activities?.map((item) => {
          const Icon = activityIcons[item.activity_type] || Activity
          return (
            <Card key={item.id} className="transition-colors hover:bg-accent/50">
              <CardContent className="flex items-start gap-4 p-4">
                <Avatar fallback={item.actor_email?.[0]?.toUpperCase() || "?"} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Icon className="h-4 w-4 shrink-0 text-muted-foreground" />
                    <span className="font-medium text-sm">{item.title}</span>
                    <Badge variant="secondary" className="ml-auto shrink-0 text-xs">
                      {item.activity_type.replace(/_/g, " ")}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-2">{item.description}</p>
                  <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
                    <span>{formatRelativeTime(item.created_at)}</span>
                    {item.reaction_count !== undefined && <span>{item.reaction_count} reactions</span>}
                    {item.comment_count !== undefined && <span>{item.comment_count} comments</span>}
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
