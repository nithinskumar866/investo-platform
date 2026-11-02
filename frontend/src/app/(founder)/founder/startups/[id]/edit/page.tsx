"use client"

import Link from "next/link"
import { useParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { StartupForm } from "@/components/startups/startup-form"
import { StartupDocuments } from "@/components/startups/startup-documents"
import { useStartup } from "@/hooks/use-api"

export default function EditStartupPage() {
  const id = Number(useParams<{ id: string }>().id)
  const { data: startup, isLoading, error } = useStartup(id)

  if (isLoading) return <Skeleton className="mx-auto h-96 max-w-2xl" />
  if (error || !startup) {
    return (
      <div className="py-16 text-center">
        <p className="text-muted-foreground">This startup could not be loaded.</p>
        <Button asChild variant="outline" className="mt-4"><Link href="/founder/startups">Back to My Startups</Link></Button>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Edit {startup.name}</h1>
        <p className="capitalize text-muted-foreground">Status: {startup.status}</p>
      </div>
      <StartupForm key={startup.updated_at} startup={startup} />
      <StartupDocuments startupId={startup.id} />
    </div>
  )
}
