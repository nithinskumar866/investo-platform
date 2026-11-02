"use client"

import Link from "next/link"
import { Download, FolderOpen, FileText } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useInvestorDocuments, useInvestorRooms } from "@/hooks/use-api"
import { humanize } from "@/lib/constants"
import { formatFileSize, formatRelativeTime } from "@/lib/utils"
import { api, mediaUrl } from "@/services/api"

const statusVariant = { none: "outline", pending: "warning", approved: "success", denied: "destructive" } as const

export default function InvestorDataRoomPage() {
  const { data: docs, isLoading: docsLoading } = useInvestorDocuments()
  const { data: rooms, isLoading: roomsLoading } = useInvestorRooms()

  const requested = (rooms ?? []).filter((r) => r.access_status !== "none")
  const roomTitle = (id: number) => {
    const room = rooms?.find((r) => r.id === id)
    return room ? `${room.startup_name}: ${room.title}` : `Room #${id}`
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Data Room</h1>
        <p className="text-muted-foreground">Documents founders have shared with you</p>
      </div>

      <Card>
        <CardHeader><CardTitle>Your documents</CardTitle></CardHeader>
        <CardContent>
          {docsLoading ? (
            <Skeleton className="h-24 w-full" />
          ) : !docs?.length ? (
            <div className="flex flex-col items-center gap-2 py-8 text-center text-muted-foreground">
              <FolderOpen className="h-10 w-10" />
              <p className="text-sm">No documents yet. Request access from a startup&apos;s page.</p>
              <Button asChild variant="outline" size="sm"><Link href="/investor/discover">Discover startups</Link></Button>
            </div>
          ) : (
            <ul className="divide-y" aria-label="Accessible documents">
              {docs.map((doc) => (
                <li key={doc.id} className="flex items-center justify-between gap-3 py-3">
                  <div className="flex min-w-0 items-center gap-3">
                    <FileText className="h-5 w-5 shrink-0 text-muted-foreground" />
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{doc.title}</p>
                      <p className="truncate text-xs text-muted-foreground">
                        {roomTitle(doc.data_room)} &middot; <span className="capitalize">{humanize(doc.document_type)}</span> &middot; {formatFileSize(doc.file_size)} &middot; {formatRelativeTime(doc.created_at)}
                      </p>
                    </div>
                  </div>
                  {doc.signed_url && (
                    <Button variant="outline" size="sm" asChild>
                      <a href={mediaUrl(doc.signed_url) ?? "#"} target="_blank" rel="noopener noreferrer"
                        onClick={() => { api.post(`/data-room/investor/documents/${doc.id}/view/`, {}).catch(() => {}) }}>
                        <Download className="mr-1 h-3 w-3" /> Open
                      </a>
                    </Button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Your access requests</CardTitle></CardHeader>
        <CardContent>
          {roomsLoading ? (
            <Skeleton className="h-16 w-full" />
          ) : !requested.length ? (
            <p className="py-4 text-center text-sm text-muted-foreground">You have not requested access to any data room.</p>
          ) : (
            <ul className="divide-y">
              {requested.map((room) => (
                <li key={room.id} className="flex items-center justify-between gap-2 py-3">
                  <div className="min-w-0">
                    <Link href={`/startup/${room.startup_id}`} className="text-sm font-medium hover:underline">{room.startup_name}</Link>
                    <p className="truncate text-xs text-muted-foreground">{room.title}</p>
                  </div>
                  <Badge variant={statusVariant[room.access_status]}>{room.access_status}</Badge>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
