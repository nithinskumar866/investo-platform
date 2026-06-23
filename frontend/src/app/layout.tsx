import type { Metadata } from "next"
import { Providers } from "@/components/layout/providers"
import "./globals.css"

export const metadata: Metadata = {
  title: "Investo - Venture Capital & Startup Platform",
  description: "Connect entrepreneurs and investors to build the next generation of startups",
  openGraph: {
    title: "Investo",
    description: "Venture Capital & Startup Ecosystem Platform",
    type: "website",
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning className="dark">
      <body className="min-h-screen bg-background text-foreground antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
