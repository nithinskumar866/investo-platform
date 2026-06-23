"use client"

import { MainLayout } from "@/components/layout/main-layout"
import { useConversations } from "@/hooks/use-api"
import { cn, formatRelativeTime } from "@/lib/utils"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { MessageSquare } from "lucide-react"
import Link from "next/link"
import { useParams, usePathname } from "next/navigation"

function ConversationSkeleton() {
  return (
    <div className="p-3 flex items-center gap-3">
      <Skeleton className="h-10 w-10 rounded-full" />
      <div className="flex-1 space-y-1.5">
        <Skeleton className="h-4 w-2/3" />
        <Skeleton className="h-3 w-full" />
      </div>
    </div>
  )
}

export default function ChatLayout({ children }: { children: React.ReactNode }) {
  const { data: conversations, isLoading } = useConversations()
  const pathname = usePathname()

  return (
    <MainLayout>
      <div className="flex h-[calc(100vh-6rem)] gap-0 rounded-xl border border-border overflow-hidden bg-card">
        <aside className="w-80 shrink-0 border-r border-border flex flex-col">
          <div className="flex items-center gap-2 border-b border-border p-4">
            <MessageSquare className="h-5 w-5 text-primary" />
            <h2 className="font-semibold">Conversations</h2>
          </div>
          <div className="flex-1 overflow-y-auto">
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => <ConversationSkeleton key={i} />)
            ) : (
              conversations?.map((conv) => {
                const active = pathname === `/chat/${conv.id}`
                const lastMsg = conv.last_message
                return (
                  <Link
                    key={conv.id}
                    href={`/chat/${conv.id}`}
                    className={cn(
                      "flex items-start gap-3 p-3 transition-colors hover:bg-accent/50 border-b border-border/50",
                      active && "bg-accent",
                    )}
                  >
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-medium text-primary">
                      {lastMsg?.sender_name?.[0] || "?"}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-medium truncate">{lastMsg?.sender_name || `User ${conv.created_by}`}</p>
                        {lastMsg && (
                          <span className="text-xs text-muted-foreground shrink-0">
                            {formatRelativeTime(lastMsg.created_at)}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground truncate mt-0.5">
                        {lastMsg?.content || "No messages yet"}
                      </p>
                    </div>
                    {!lastMsg?.read_by?.includes(conv.created_by) && (
                      <Badge className="h-2 w-2 rounded-full p-0" />
                    )}
                  </Link>
                )
              })
            )}
          </div>
        </aside>
        <div className="flex-1 flex flex-col">{children}</div>
      </div>
    </MainLayout>
  )
}
