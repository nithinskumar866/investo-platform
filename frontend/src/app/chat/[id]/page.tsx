"use client"

import { useState, useRef, useEffect } from "react"
import { useParams } from "next/navigation"
import { useMessages } from "@/hooks/use-api"
import { useAuthStore } from "@/stores/auth"
import { formatRelativeTime } from "@/lib/utils"
import { Avatar } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { Send, ArrowDown, Loader2 } from "lucide-react"

function MessageSkeleton() {
  return (
    <div className="flex items-end gap-2 p-3">
      <Skeleton className="h-8 w-8 rounded-full" />
      <Skeleton className="h-10 w-48 rounded-lg" />
    </div>
  )
}

export default function ChatConversationPage() {
  const { id } = useParams<{ id: string }>()
  const conversationId = Number(id)
  const { data: messages, isLoading } = useMessages(conversationId)
  const { user } = useAuthStore()
  const [input, setInput] = useState("")
  const [sending, setSending] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || sending) return
    setSending(true)
    try {
      const { api } = await import("@/services/api")
      await api.post(`/chat/conversations/${conversationId}/messages/`, { content: input.trim() })
      setInput("")
    } finally {
      setSending(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex flex-col flex-1 p-4">
        <div className="flex-1 space-y-4">
          {Array.from({ length: 5 }).map((_, i) => <MessageSkeleton key={i} />)}
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col flex-1">
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages?.length === 0 && (
          <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
            No messages yet. Start the conversation!
          </div>
        )}
        {messages?.map((msg) => {
          const isOwn = msg.sender === user?.id
          return (
            <div key={msg.id} className={`flex items-end gap-2 ${isOwn ? "flex-row-reverse" : ""}`}>
              {!isOwn && <Avatar fallback={msg.sender_name?.[0] || "?"} className="h-8 w-8" />}
              <div className={`max-w-[70%] ${isOwn ? "items-end" : "items-start"} flex flex-col`}>
                <div
                  className={`rounded-2xl px-4 py-2 text-sm ${
                    isOwn
                      ? "bg-primary text-primary-foreground rounded-br-md"
                      : "bg-muted text-foreground rounded-bl-md"
                  }`}
                >
                  {msg.content}
                </div>
                <span className="mt-0.5 text-[10px] text-muted-foreground px-1">
                  {formatRelativeTime(msg.created_at)}
                </span>
              </div>
            </div>
          )
        })}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-border p-4">
        <form
          onSubmit={(e) => { e.preventDefault(); handleSend() }}
          className="flex items-center gap-2"
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            className="flex-1"
            disabled={sending}
          />
          <Button type="submit" size="icon" disabled={!input.trim() || sending}>
            {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </form>
      </div>
    </div>
  )
}
