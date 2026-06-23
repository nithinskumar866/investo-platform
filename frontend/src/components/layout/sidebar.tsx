"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useAuthStore } from "@/stores/auth"
import { useUIStore } from "@/stores/ui"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Avatar } from "@/components/ui/avatar"
import {
  LayoutDashboard, Building2, Search, MessageSquare, Calendar,
  TrendingUp, FileText, Bell, CreditCard, Shield, Users,
  Activity, Settings, Menu, X, LogOut, ChevronLeft, ChevronRight,
  Briefcase, Lightbulb, PieChart, UserCheck, Layers,
} from "lucide-react"

const founderNav = [
  { href: "/founder", label: "Dashboard", icon: LayoutDashboard },
  { href: "/founder/startups", label: "Startups", icon: Building2 },
  { href: "/founder/analytics", label: "Analytics", icon: TrendingUp },
  { href: "/founder/discover", label: "Discover Investors", icon: Search },
  { href: "/founder/matches", label: "Matches", icon: UserCheck },
  { href: "/founder/insights", label: "AI Insights", icon: Lightbulb },
  { href: "/chat", label: "Messages", icon: MessageSquare },
  { href: "/meetings", label: "Meetings", icon: Calendar },
  { href: "/founder/deals", label: "Deal Pipeline", icon: Briefcase },
  { href: "/founder/data-room", label: "Data Room", icon: FileText },
  { href: "/billing", label: "Billing", icon: CreditCard },
]

const investorNav = [
  { href: "/investor", label: "Dashboard", icon: LayoutDashboard },
  { href: "/investor/discover", label: "Discover Startups", icon: Search },
  { href: "/investor/saved", label: "Saved Startups", icon: Layers },
  { href: "/investor/matches", label: "Matches", icon: UserCheck },
  { href: "/investor/insights", label: "AI Insights", icon: Lightbulb },
  { href: "/chat", label: "Messages", icon: MessageSquare },
  { href: "/meetings", label: "Meetings", icon: Calendar },
  { href: "/investor/deals", label: "Deal Pipeline", icon: Briefcase },
  { href: "/investor/analytics", label: "Analytics", icon: PieChart },
  { href: "/billing", label: "Billing", icon: CreditCard },
]

const discoveryNav = [
  { href: "/feed", label: "Activity Feed", icon: Activity },
  { href: "/search", label: "Search", icon: Search },
  { href: "/trending", label: "Trending", icon: TrendingUp },
]

const adminNav = [
  { href: "/admin", label: "Dashboard", icon: Shield },
  { href: "/admin/users", label: "Users", icon: Users },
  { href: "/admin/startups", label: "Moderation", icon: Building2 },
  { href: "/admin/tickets", label: "Tickets", icon: MessageSquare },
  { href: "/admin/revenue", label: "Revenue", icon: CreditCard },
  { href: "/admin/audit", label: "Audit Logs", icon: FileText },
  { href: "/admin/risk", label: "Risk", icon: Activity },
  { href: "/admin/ops", label: "Observability", icon: Activity },
]

export function Sidebar() {
  const pathname = usePathname()
  const { sidebarOpen, toggleSidebar } = useUIStore()
  const { user } = useAuthStore()
  const role = user?.role

  let navItems = discoveryNav
  if (role === "entrepreneur") navItems = [...founderNav, ...discoveryNav]
  else if (role === "investor") navItems = [...investorNav, ...discoveryNav]
  else if (role === "admin") navItems = adminNav

  return (
    <aside className={cn(
      "fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-border bg-card transition-all duration-300",
      sidebarOpen ? "w-64" : "w-16",
    )}>
      <div className="flex h-14 items-center border-b border-border px-4">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-gradient-to-br from-emerald-400 to-emerald-600 shadow-sm">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="22,12 18,12 15,21 9,3 6,12 2,12" />
            </svg>
          </div>
          {sidebarOpen && <span className="text-base font-bold tracking-tight text-foreground">Investo</span>}
        </div>
        <Button variant="ghost" size="icon" onClick={toggleSidebar} className="ml-auto h-6 w-6 text-muted-foreground">
          {sidebarOpen ? <ChevronLeft className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        </Button>
      </div>
      <nav className="flex-1 overflow-y-auto p-2 space-y-1">
        {navItems.map((item) => {
          const active = pathname === item.href || pathname.startsWith(item.href + "/")
          return (
            <Link key={item.href} href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-accent",
                active ? "bg-accent text-accent-foreground font-medium" : "text-muted-foreground",
              )}>
              <item.icon className="h-4 w-4 shrink-0" />
              {sidebarOpen && <span>{item.label}</span>}
            </Link>
          )
        })}
      </nav>
      <div className="border-t border-border p-3">
        <Link href="/notifications" className={cn(
          "flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-accent transition-colors",
          pathname === "/notifications" && "bg-accent",
        )}>
          <Bell className="h-4 w-4" />
          {sidebarOpen && <span>Notifications</span>}
        </Link>
      </div>
    </aside>
  )
}

export function Topbar() {
  const { toggleSidebar, toggleCommandPalette } = useUIStore()
  const { user, logout } = useAuthStore()

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b border-border bg-background px-4 lg:px-6">
      <Button variant="ghost" size="icon" onClick={toggleSidebar} className="md:hidden">
        <Menu className="h-5 w-5" />
      </Button>
      <div className="flex-1" />
      <Button variant="ghost" size="sm" onClick={toggleCommandPalette} className="text-muted-foreground gap-2">
        <kbd className="pointer-events-none hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium opacity-100 sm:flex">
          <span className="text-xs">⌘</span>K
        </kbd>
        <Search className="h-4 w-4" />
      </Button>
      <div className="flex items-center gap-2">
        <span className="hidden text-sm text-muted-foreground md:inline">{user?.email}</span>
        <Button variant="ghost" size="icon" onClick={logout}>
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  )
}
