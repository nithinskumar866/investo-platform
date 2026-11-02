"use client"

import { MutationCache, QueryCache, QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useState, useEffect } from "react"
import { useUIStore } from "@/stores/ui"
import { useAuthStore } from "@/stores/auth"
import { toast, Toaster } from "sonner"

function ThemeProvider({ children }: { children: React.ReactNode }) {
  const theme = useUIStore((s) => s.theme)

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark")
  }, [theme])

  return <>{children}</>
}

function AuthBootstrap() {
  const init = useAuthStore((s) => s.init)
  useEffect(() => { init() }, [init])
  return null
}

/** Every failed query or mutation surfaces its API message, unless the caller shows it inline. */
const reportError = (error: Error, meta?: Record<string, unknown>) => {
  if (!meta?.silent) toast.error(error.message, { id: error.message })
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        queryCache: new QueryCache({ onError: (error, query) => reportError(error, query.meta) }),
        mutationCache: new MutationCache({ onError: (error, _v, _c, mutation) => reportError(error, mutation.meta) }),
        defaultOptions: {
          queries: {
            staleTime: 30 * 1000,
            refetchOnWindowFocus: false,
            retry: (count, error: any) => count < 1 && !(error?.status >= 400 && error?.status < 500),
          },
        },
      }),
  )

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthBootstrap />
        {children}
        <Toaster
          position="top-right"
          toastOptions={{
            style: { background: "hsl(var(--card))", color: "hsl(var(--card-foreground))", border: "1px solid hsl(var(--border))" },
          }}
        />
      </ThemeProvider>
    </QueryClientProvider>
  )
}
