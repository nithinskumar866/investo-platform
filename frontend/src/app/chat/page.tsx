"use client"

import { useEffect, useRef, useState, Suspense } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { MessageSquare, Loader2 } from "lucide-react"
import { useCreateConversation } from "@/hooks/use-api"

function ChatEmptyContent() {
  const searchParams = useSearchParams()
  const participantId = searchParams.get("participant")
  const router = useRouter()
  const { mutateAsync: createConversation } = useCreateConversation()
  const [isPending, setIsPending] = useState(!!participantId)
  const [error, setError] = useState<string | null>(null)
  const started = useRef<string | null>(null)

  useEffect(() => {
    // The ref stops React strict mode's double effect from opening two conversations.
    if (!participantId || started.current === participantId) return
    started.current = participantId
    createConversation({ participant_id: Number(participantId) })
      .then((res) => router.replace(`/chat/${res.id}`))
      .catch((err: Error) => {
        setError(err.message)
        setIsPending(false)
      })
  }, [participantId, createConversation, router])

  if (isPending) {
    return (
      <div className="flex flex-1 items-center justify-center" role="status" aria-label="Opening conversation">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="flex flex-1 items-center justify-center">
      <div className="flex flex-col items-center gap-3 p-8 text-muted-foreground">
        <MessageSquare className="h-16 w-16" />
        {error ? (
          <>
            <h2 className="text-xl font-semibold">Could not start this conversation</h2>
            <p role="alert" className="max-w-xs text-center text-sm">{error}</p>
          </>
        ) : (
          <>
            <h2 className="text-xl font-semibold">Select a conversation</h2>
            <p className="max-w-xs text-center text-sm">Choose a conversation from the list to start chatting</p>
          </>
        )}
      </div>
    </div>
  )
}

export default function ChatEmptyPage() {
  return (
    <Suspense fallback={
      <div className="flex flex-1 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    }>
      <ChatEmptyContent />
    </Suspense>
  )
}
