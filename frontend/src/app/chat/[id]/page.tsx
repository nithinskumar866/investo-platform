"use client"

import { useState, useRef, useEffect } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { useMessages, useSendMessage } from "@/hooks/use-api"
import { useAuthStore } from "@/stores/auth"
import { formatRelativeTime } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { ArrowLeft, Send, Loader2 } from "lucide-react"

export default function ChatConversationPage() {
  const { id } = useParams<{ id: string }>()
  const conversationId = Number(id)
  const { data: messages, isLoading, error } = useMessages(conversationId)
  const send = useSendMessage(conversationId)
  const { user } = useAuthStore()
  const [input, setInput] = useState("")
  const bottomRef = useRef<HTMLDivElement>(null)

  const count = messages?.length ?? 0
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [count])

  const handleSend = () => {
    const content = input.trim()
    if (!content || send.isPending) return
    send.mutate(content, { onSuccess: () => setInput("") })
  }

  const backLink = (
    <div className="border-b border-border p-2 md:hidden">
      <Button variant="ghost" size="sm" asChild>
        <Link href="/chat"><ArrowLeft className="mr-1 h-4 w-4" /> Conversations</Link>
      </Button>
    </div>
  )

  if (isLoading) {
    return (
      <div className="flex flex-1 flex-col space-y-4 p-4">
        {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10 w-48 rounded-lg" />)}
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-1 flex-col">
        {backLink}
        <div className="flex flex-1 items-center justify-center p-6 text-center text-sm text-muted-foreground">
          This conversation could not be loaded.
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {backLink}
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages?.length === 0 && (
          <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
            No messages yet. Start the conversation!
          </div>
        )}
        {messages?.map((msg) => {
          const isOwn = (msg.sender?.id ?? msg.sender_id) === user?.id
          return (
            <div key={msg.id} className={`flex items-end gap-2 ${isOwn ? "flex-row-reverse" : ""}`} data-own={isOwn}>
              <div className={`flex max-w-[85%] flex-col sm:max-w-[70%] ${isOwn ? "items-end" : "items-start"}`}>
                <div className={`rounded-2xl px-4 py-2 text-sm ${isOwn ? "rounded-br-md bg-primary text-primary-foreground" : "rounded-bl-md bg-muted text-foreground"}`}>
                  {msg.content}
                </div>
                <span className="mt-0.5 px-1 text-[10px] text-muted-foreground">{formatRelativeTime(msg.created_at)}</span>
              </div>
            </div>
          )
        })}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-border p-3 sm:p-4">
        <form onSubmit={(e) => { e.preventDefault(); handleSend() }} className="flex items-center gap-2">
          <Input
            aria-label="Message"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            className="flex-1"
            disabled={send.isPending}
          />
          <Button type="submit" size="icon" aria-label="Send message" disabled={!input.trim() || send.isPending}>
            {send.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </form>
      </div>
    </div>
  )
}
