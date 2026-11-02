"use client"

import { useState } from "react"
import { toast } from "sonner"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Avatar } from "@/components/ui/avatar"
import { Skeleton } from "@/components/ui/skeleton"
import { useAdminUserAction, useAdminUsers } from "@/hooks/use-api"
import { useDebounce } from "@/hooks/use-debounce"
import { useAuthStore } from "@/stores/auth"
import { getInitials } from "@/lib/utils"
import { BadgeCheck, Search, Shield, ShieldOff } from "lucide-react"

export default function AdminUsersPage() {
  const [search, setSearch] = useState("")
  const [roleFilter, setRoleFilter] = useState("all")
  const debounced = useDebounce(search)
  const me = useAuthStore((s) => s.user)
  const { data: users, isLoading } = useAdminUsers({ query: debounced || undefined, role: roleFilter !== "all" ? roleFilter : undefined })
  const action = useAdminUserAction()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">User Management</h1>
        <p className="text-muted-foreground">Suspend, restore and verify platform users</p>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative max-w-sm flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input aria-label="Search users" placeholder="Search users..." className="pl-9" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <div className="flex flex-wrap gap-2">
          {["all", "entrepreneur", "investor", "admin"].map((role) => (
            <Button key={role} variant={roleFilter === role ? "default" : "outline"} size="sm" onClick={() => setRoleFilter(role)}>
              {role.charAt(0).toUpperCase() + role.slice(1)}
            </Button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-16 w-full" />)}
        </div>
      ) : !users?.length ? (
        <Card><CardContent className="py-12 text-center text-sm text-muted-foreground">No users match your search.</CardContent></Card>
      ) : (
        <Card>
          <div className="divide-y">
            {users.map((user) => {
              const name = `${user.first_name} ${user.last_name}`.trim() || user.email
              return (
                <div key={user.id} className="flex flex-wrap items-center justify-between gap-3 p-4" data-testid={`user-${user.email}`}>
                  <div className="flex min-w-0 items-center gap-3">
                    <Avatar fallback={getInitials(name)} />
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{name}</p>
                      <p className="truncate text-xs text-muted-foreground">{user.email}</p>
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant={user.role === "admin" ? "default" : user.role === "investor" ? "warning" : "secondary"}>{user.role}</Badge>
                    {user.is_verified && <Badge variant="success">Verified</Badge>}
                    <Badge variant={user.is_active ? "success" : "destructive"}>{user.is_active ? "Active" : "Suspended"}</Badge>
                    {!user.is_verified && (
                      <Button variant="outline" size="sm" disabled={action.isPending}
                        onClick={() => action.mutate({ id: user.id, action: "verify", body: { verified: true } }, { onSuccess: () => toast.success(`${user.email} verified`) })}>
                        <BadgeCheck className="mr-1 h-3 w-3" /> Verify
                      </Button>
                    )}
                    {user.id !== me?.id && (
                      user.is_active ? (
                        <Button variant="outline" size="sm" disabled={action.isPending}
                          onClick={() => {
                            if (confirm(`Suspend ${user.email}? They will not be able to sign in.`)) {
                              action.mutate({ id: user.id, action: "suspend" }, { onSuccess: () => toast.success(`${user.email} suspended`) })
                            }
                          }}>
                          <ShieldOff className="mr-1 h-3 w-3" /> Suspend
                        </Button>
                      ) : (
                        <Button variant="outline" size="sm" disabled={action.isPending}
                          onClick={() => action.mutate({ id: user.id, action: "restore" }, { onSuccess: () => toast.success(`${user.email} restored`) })}>
                          <Shield className="mr-1 h-3 w-3" /> Restore
                        </Button>
                      )
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </Card>
      )}
    </div>
  )
}
