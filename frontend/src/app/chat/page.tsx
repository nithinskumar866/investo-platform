"use client"

import { useEffect, Suspense } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Card } from "@/components/ui/card"
import { MessageSquare, Loader2 } from "lucide-react"
import { useCreateConversation } from "@/hooks/use-api"

function ChatEmptyContent() {
  const searchParams = useSearchParams()
  const participantId = searchParams.get("participant")
  const router = useRouter()
  const { mutate: createConversation, isPending } = useCreateConversation()

  useEffect(() => {
    if (participantId) {
      createConversation(
        { participant_id: Number(participantId) },
        {
          onSuccess: (res) => {
            if (res.id) {
              router.replace(`/chat/${res.id}`)
            }
          },
          onError: () => {
            // fallback if it fails
            router.replace("/chat")
          }
        }
      )
    }
  }, [participantId, createConversation, router])

  if (isPending) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="flex flex-1 items-center justify-center">
      <Card className="border-none shadow-none bg-transparent">
        <div className="flex flex-col items-center gap-3 text-muted-foreground p-8">
          <MessageSquare className="h-16 w-16" />
          <h2 className="text-xl font-semibold">Select a conversation</h2>
          <p className="text-sm text-center max-w-xs">
            Choose a conversation from the sidebar to start chatting
          </p>
        </div>
      </Card>
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
