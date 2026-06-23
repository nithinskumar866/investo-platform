"use client"

import { Card } from "@/components/ui/card"
import { MessageSquare } from "lucide-react"

export default function ChatEmptyPage() {
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
