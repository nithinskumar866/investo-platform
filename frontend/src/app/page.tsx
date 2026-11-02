"use client"

import { useEffect } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { ArrowRight, Building2, CalendarCheck, FolderLock, Handshake, Search, Sparkles, TrendingUp, Upload } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useAuthStore } from "@/stores/auth"
import { dashboardPath } from "@/lib/utils"

const founderSteps = [
  { icon: Building2, title: "Create your startup", text: "Build a profile with your pitch, team and metrics, then publish it to investors." },
  { icon: Upload, title: "Open a data room", text: "Upload documents and approve who gets to read them." },
  { icon: Handshake, title: "Close your round", text: "Track interested investors, accept a term sheet and watch your funding progress." },
]

const investorSteps = [
  { icon: Search, title: "Discover startups", text: "Search and filter published startups, ranked by how well they match you." },
  { icon: Sparkles, title: "Understand the match", text: "Read an AI explanation of the strengths and risks behind each match." },
  { icon: TrendingUp, title: "Run your pipeline", text: "Express interest, meet founders, send a term sheet and close the deal." },
]

function Steps({ title, steps }: { title: string; steps: typeof founderSteps }) {
  return (
    <div>
      <h3 className="mb-6 text-lg font-semibold text-emerald-400">{title}</h3>
      <ol className="space-y-6">
        {steps.map((step) => (
          <li key={step.title} className="flex gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10">
              <step.icon className="h-5 w-5 text-emerald-400" />
            </div>
            <div>
              <p className="font-medium text-white">{step.title}</p>
              <p className="mt-1 text-sm text-white/60">{step.text}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  )
}

export default function HomePage() {
  const router = useRouter()
  const { user, initialized } = useAuthStore()

  useEffect(() => {
    if (initialized && user) router.replace(dashboardPath(user.role))
  }, [initialized, user, router])

  // Avoid flashing the marketing page at signed-in users on their way to the dashboard.
  if (!initialized || user) return <div className="min-h-screen bg-[#060b18]" />

  return (
    <div className="min-h-screen bg-[#060b18] text-white">
      <header className="mx-auto flex max-w-6xl items-center justify-between p-6">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-gradient-to-br from-emerald-400 to-emerald-600">
            <CalendarCheck className="h-4 w-4 text-white" />
          </div>
          <span className="text-lg font-bold tracking-tight">Investo</span>
        </div>
        <nav className="flex items-center gap-2">
          <Button variant="ghost" asChild className="text-white hover:bg-white/10 hover:text-white">
            <Link href="/auth/login">Sign in</Link>
          </Button>
          <Button asChild className="bg-emerald-500 text-white hover:bg-emerald-400">
            <Link href="/auth/register">Get started</Link>
          </Button>
        </nav>
      </header>

      <main>
        <section className="mx-auto max-w-4xl px-6 py-20 text-center">
          <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">Where founders and investors close deals</h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-white/60">
            Investo matches startups with the right investors, then gives both sides one place for chat, meetings, data rooms and the deal pipeline.
          </p>
          <div className="mt-10 flex flex-wrap justify-center gap-3">
            <Button size="lg" asChild className="bg-emerald-500 text-white hover:bg-emerald-400">
              <Link href="/auth/register">Create a free account <ArrowRight className="ml-2 h-4 w-4" /></Link>
            </Button>
            <Button size="lg" variant="outline" asChild className="border-white/20 text-white hover:bg-white/10 hover:text-white">
              <Link href="/auth/login">Sign in</Link>
            </Button>
          </div>
        </section>

        <section className="border-y border-white/5 bg-white/[0.02] py-20" aria-labelledby="how-it-works">
          <div className="mx-auto max-w-5xl px-6">
            <h2 id="how-it-works" className="mb-12 text-center text-3xl font-bold tracking-tight">How it works</h2>
            <div className="grid gap-12 md:grid-cols-2">
              <Steps title="For founders" steps={founderSteps} />
              <Steps title="For investors" steps={investorSteps} />
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-3xl px-6 py-20 text-center">
          <FolderLock className="mx-auto mb-4 h-8 w-8 text-emerald-400" />
          <h2 className="text-3xl font-bold tracking-tight">Ready to start?</h2>
          <p className="mt-4 text-white/60">This is a student demo project: all money on the platform is dummy money, and no real payment is ever taken.</p>
          <Button size="lg" asChild className="mt-8 bg-emerald-500 text-white hover:bg-emerald-400">
            <Link href="/auth/register">Join Investo</Link>
          </Button>
        </section>
      </main>

      <footer className="border-t border-white/5 py-6 text-center text-xs text-white/40">
        &copy; {new Date().getFullYear()} Investo
      </footer>
    </div>
  )
}
