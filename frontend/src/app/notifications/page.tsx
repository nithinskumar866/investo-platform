"use client"

import { useNotifications, useUnreadCount, useMarkRead } from "@/hooks/use-api"
import { cn, formatRelativeTime } from "@/lib/utils"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Bell, CheckCheck, Info, AlertTriangle, CheckCircle, XCircle,
  MessageSquare, Building2, Handshake, DollarSign, Calendar, Star, ArrowRight,
} from "lucide-react"

const typeIcons: Record<string, React.ElementType> = {
  info: Info, warning: AlertTriangle, success: CheckCircle, error: XCircle,
  message: MessageSquare, match: Handshake, investment: DollarSign,
  meeting: Calendar, milestone: Star, startup: Building2,
}

function NotificationSkeleton() {
  return (
    <div className="flex items-start gap-3 p-4 border-b border-border/50">
      <Skeleton className="h-9 w-9 rounded-full" />
      <div className="flex-1 space-y-1.5">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    </div>
  )
}

export default function NotificationsPage() {
  const { data: notifications, isLoading } = useNotifications()
  const { data: unread } = useUnreadCount()
  const markRead = useMarkRead()

  if (isLoading) {
    return (
      <div className="mx-auto max-w-2xl">
        <Skeleton className="mb-6 h-7 w-48" />
        <Card>
          {Array.from({ length: 6 }).map((_, i) => <NotificationSkeleton key={i} />)}
        </Card>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bell className="h-5 w-5 text-primary" />
          <h1 className="text-2xl font-bold">Notifications</h1>
          {unread?.count ? (
            <Badge variant="default" className="ml-2">{unread.count} unread</Badge>
          ) : null}
        </div>
      </div>

      <Card>
        {notifications?.length === 0 ? (
          <CardContent className="flex flex-col items-center gap-2 py-16 text-muted-foreground">
            <Bell className="h-12 w-12" />
            <p className="text-sm">No notifications yet</p>
          </CardContent>
        ) : (
          <div>
            {notifications?.map((notif) => {
              const Icon = typeIcons[notif.type] || Bell
              return (
                <div
                  key={notif.id}
                  className={cn(
                    "flex items-start gap-3 p-4 border-b border-border/50 transition-colors hover:bg-accent/50",
                    !notif.is_read && "bg-primary/5",
                  )}
                >
                  <div className={cn(
                    "flex h-9 w-9 shrink-0 items-center justify-center rounded-full",
                    notif.is_read ? "bg-muted text-muted-foreground" : "bg-primary/10 text-primary",
                  )}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <p className={cn("text-sm", !notif.is_read && "font-medium")}>{notif.title}</p>
                      <span className="shrink-0 text-[10px] text-muted-foreground">
                        {formatRelativeTime(notif.created_at)}
                      </span>
                    </div>
                    <p className="mt-0.5 text-xs text-muted-foreground line-clamp-2">{notif.message}</p>
                    {!notif.is_read && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="mt-1.5 h-7 text-xs gap-1"
                        onClick={() => markRead.mutate(notif.id)}
                      >
                        <CheckCheck className="h-3 w-3" /> Mark read
                      </Button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </Card>
    </div>
  )
}
