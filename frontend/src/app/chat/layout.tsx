"use client"

import { MainLayout } from "@/components/layout/main-layout"
import { useConversations } from "@/hooks/use-api"
import { cn, formatRelativeTime } from "@/lib/utils"
import { Skeleton } from "@/components/ui/skeleton"
import { MessageSquare } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"

function ConversationSkeleton() {
  return (
    <div className="flex items-center gap-3 p-3">
      <Skeleton className="h-10 w-10 rounded-full" />
      <div className="flex-1 space-y-1.5">
        <Skeleton className="h-4 w-2/3" />
        <Skeleton className="h-3 w-full" />
      </div>
    </div>
  )
}

/** Split out of the layout so it only fetches once the auth guard in MainLayout has passed. */
function ChatShell({ children }: { children: React.ReactNode }) {
  const { data: conversations, isLoading } = useConversations()
  const pathname = usePathname()
  const inThread = pathname !== "/chat"

  return (
    <div className="flex h-[calc(100vh-6rem)] overflow-hidden rounded-xl border border-border bg-card">
      {/* On small screens only one pane shows: the list, or the open thread. */}
      <aside className={cn("w-full shrink-0 flex-col border-r border-border md:flex md:w-80", inThread ? "hidden" : "flex")}>
        <div className="flex items-center gap-2 border-b border-border p-4">
          <MessageSquare className="h-5 w-5 text-primary" />
          <h2 className="font-semibold">Conversations</h2>
        </div>
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            Array.from({ length: 5 }).map((_, i) => <ConversationSkeleton key={i} />)
          ) : !conversations?.length ? (
            <p className="p-6 text-center text-sm text-muted-foreground">
              No conversations yet. Use Message on a match to start one.
            </p>
          ) : (
            conversations.map((conv) => {
              const active = pathname === `/chat/${conv.id}`
              const lastMsg = conv.latest_message
              const other = conv.other_participant
              const displayName = other ? (`${other.first_name} ${other.last_name}`.trim() || other.email || "Unknown") : "Unknown User"
              return (
                <Link
                  key={conv.id}
                  href={`/chat/${conv.id}`}
                  className={cn("flex items-start gap-3 border-b border-border/50 p-3 transition-colors hover:bg-accent/10", active && "bg-accent/20")}
                >
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-medium text-primary">
                    {displayName[0]}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <p className="truncate text-sm font-medium">{displayName}</p>
                      {lastMsg && <span className="shrink-0 text-xs text-muted-foreground">{formatRelativeTime(lastMsg.created_at)}</span>}
                    </div>
                    <p className="mt-0.5 truncate text-xs text-muted-foreground">{lastMsg?.content || "No messages yet"}</p>
                  </div>
                  {conv.unread ? <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary" aria-label={`${conv.unread} unread`} /> : null}
                </Link>
              )
            })
          )}
        </div>
      </aside>
      <div className={cn("min-w-0 flex-1 flex-col md:flex", inThread ? "flex" : "hidden")}>{children}</div>
    </div>
  )
}

export default function ChatLayout({ children }: { children: React.ReactNode }) {
  return (
    <MainLayout>
      <ChatShell>{children}</ChatShell>
    </MainLayout>
  )
}
