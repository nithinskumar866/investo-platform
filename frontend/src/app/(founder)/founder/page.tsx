"use client"

import { useFounderAnalytics, useMatches, useMeetings, useFeed } from "@/hooks/use-api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Avatar } from "@/components/ui/avatar"
import {
  Eye, Handshake, CalendarCheck, DollarSign, TrendingUp, TrendingDown,
  ArrowRight,
} from "lucide-react"
import Link from "next/link"
import { formatRelativeTime, formatCurrency } from "@/lib/utils"

export default function FounderDashboard() {
  const { data: analytics, isLoading: analyticsLoading } = useFounderAnalytics()
  const { data: recentMatches, isLoading: matchesLoading } = useMatches("investor")
  const { data: meetings, isLoading: meetingsLoading } = useMeetings()
  const { data: feed, isLoading: feedLoading } = useFeed()

  const kpiCards = [
    { label: "Startup Views", key: "startup_views", icon: Eye },
    { label: "Matches", key: "matches", icon: Handshake },
    { label: "Chat Engagement", key: "chat_engagement", icon: CalendarCheck },
    { label: "Data Room", key: "data_room", icon: DollarSign },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Founder Dashboard</h1>
        <p className="text-muted-foreground">Overview of your startup&apos;s performance</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {kpiCards.map((kpi) => {
          const item = analytics?.kpi_cards?.[kpi.key]
          return (
            <Card key={kpi.label}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">{kpi.label}</CardTitle>
                <kpi.icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                {analyticsLoading ? (
                  <Skeleton className="h-8 w-20" />
                ) : (
                  <div className="flex items-center gap-2">
                    <span className="text-2xl font-bold">{item?.value ?? 0}</span>
                    {item?.growth !== undefined && (
                      <Badge variant={item.growth >= 0 ? "success" : "destructive"} className="gap-1">
                        {item.growth >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                        {Math.abs(item.growth)}%
                      </Badge>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      {analytics?.funding_progress && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Funding Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between text-sm mb-2">
              <span>Raised: {formatCurrency(analytics.funding_progress.raised)}</span>
              <span>Goal: {formatCurrency(analytics.funding_progress.goal)}</span>
            </div>
            <div className="h-2 w-full rounded-full bg-primary/20">
              <div
                className="h-2 rounded-full bg-primary transition-all"
                style={{ width: `${Math.min(analytics.funding_progress.percentage, 100)}%` }}
              />
            </div>
            <p className="text-xs text-muted-foreground mt-2">{analytics.funding_progress.percentage}% funded</p>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-medium">Recent Matches</CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/founder/matches">View All <ArrowRight className="ml-1 h-3 w-3" /></Link>
            </Button>
          </CardHeader>
          <CardContent>
            {matchesLoading ? (
              <div className="space-y-3">{[1, 2, 3].map((i) => <Skeleton key={i} className="h-12 w-full" />)}</div>
            ) : recentMatches?.slice(0, 5).map((match) => (
              <div key={match.id} className="flex items-center gap-3 py-2 border-b last:border-0">
                <Avatar fallback={match.investor_detail?.first_name?.[0] ?? "I"} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">
                    {match.investor_detail
                      ? `${match.investor_detail.first_name} ${match.investor_detail.last_name}`
                      : `Investor #${match.investor}`}
                  </p>
                  <p className="text-xs text-muted-foreground">{match.status}</p>
                </div>
                <Badge variant={match.score >= 80 ? "success" : match.score >= 50 ? "warning" : "secondary"}>
                  {match.score}%
                </Badge>
              </div>
            )) ?? <p className="text-sm text-muted-foreground">No matches yet.</p>}
          </CardContent>
        </Card>

        <Card className="lg:col-span-1">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-medium">Upcoming Meetings</CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/meetings">View All <ArrowRight className="ml-1 h-3 w-3" /></Link>
            </Button>
          </CardHeader>
          <CardContent>
            {meetingsLoading ? (
              <div className="space-y-3">{[1, 2, 3].map((i) => <Skeleton key={i} className="h-12 w-full" />)}</div>
            ) : meetings?.filter((m) => new Date(m.scheduled_start) > new Date()).slice(0, 5).map((meeting) => (
              <div key={meeting.id} className="flex items-center gap-3 py-2 border-b last:border-0">
                <CalendarCheck className="h-4 w-4 text-muted-foreground shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{meeting.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(meeting.scheduled_start).toLocaleDateString()} –{" "}
                    {new Date(meeting.scheduled_end).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </p>
                </div>
                <Badge variant={meeting.status === "confirmed" ? "success" : "warning"}>{meeting.status}</Badge>
              </div>
            )) ?? <p className="text-sm text-muted-foreground">No upcoming meetings.</p>}
          </CardContent>
        </Card>

        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-sm font-medium">Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            {feedLoading ? (
              <div className="space-y-3">{[1, 2, 3].map((i) => <Skeleton key={i} className="h-12 w-full" />)}</div>
            ) : feed?.slice(0, 6).map((activity) => (
              <div key={activity.id} className="flex items-start gap-3 py-2 border-b last:border-0">
                <div className="h-2 w-2 mt-2 rounded-full bg-primary shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm">{activity.title}</p>
                  <p className="text-xs text-muted-foreground">{formatRelativeTime(activity.created_at)}</p>
                </div>
              </div>
            )) ?? <p className="text-sm text-muted-foreground">No recent activity.</p>}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
