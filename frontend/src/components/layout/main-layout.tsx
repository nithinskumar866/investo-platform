"use client"

import { useEffect } from "react"
import { usePathname, useRouter } from "next/navigation"
import { Loader2 } from "lucide-react"
import { Sidebar, Topbar } from "@/components/layout/sidebar"
import { useUIStore } from "@/stores/ui"
import { useAuthStore } from "@/stores/auth"
import { cn, dashboardPath } from "@/lib/utils"

/** App shell. Signed-out users go to login, users of another role go to their own dashboard. */
export function MainLayout({ children, roles }: { children: React.ReactNode; roles?: string[] }) {
  const { sidebarOpen } = useUIStore()
  const { user, initialized } = useAuthStore()
  const router = useRouter()
  const pathname = usePathname()

  const allowed = !!user && (!roles || roles.includes(user.role))

  useEffect(() => {
    if (!initialized || allowed) return
    if (!user) router.replace(`/auth/login?next=${encodeURIComponent(pathname)}`)
    else router.replace(dashboardPath(user.role))
  }, [initialized, allowed, user, pathname, router])

  if (!allowed) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background" role="status" aria-label="Loading">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <div className={cn("transition-all duration-300 ml-0", sidebarOpen ? "md:ml-64" : "md:ml-16")}>
        <Topbar />
        <main className="p-4 lg:p-6">{children}</main>
      </div>
    </div>
  )
}
