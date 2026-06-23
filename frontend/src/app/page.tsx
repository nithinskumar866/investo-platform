"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/stores/auth"

export default function HomePage() {
  const router = useRouter()
  const { user, isAuthenticated } = useAuthStore()

  useEffect(() => {
    if (isAuthenticated && user) {
      if (user.role === "entrepreneur") router.replace("/founder")
      else if (user.role === "investor") router.replace("/investor")
      else if (user.role === "admin") router.replace("/admin")
      else router.replace("/auth/login")
    } else {
      router.replace("/auth/login")
    }
  }, [isAuthenticated, user, router])

  return null
}
