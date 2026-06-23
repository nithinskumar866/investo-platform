"use client"

import { Sidebar, Topbar } from "@/components/layout/sidebar"
import { useUIStore } from "@/stores/ui"
import { cn } from "@/lib/utils"

export function MainLayout({ children }: { children: React.ReactNode }) {
  const { sidebarOpen } = useUIStore()

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
