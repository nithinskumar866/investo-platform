"use client"

import { MainLayout } from "@/components/layout/main-layout"

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return <MainLayout roles={["admin"]}>{children}</MainLayout>
}
