"use client"

import { StartupForm } from "@/components/startups/startup-form"

export default function NewStartupPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Create New Startup</h1>
        <p className="text-muted-foreground">Save a draft, or publish straight away.</p>
      </div>
      <StartupForm />
    </div>
  )
}
