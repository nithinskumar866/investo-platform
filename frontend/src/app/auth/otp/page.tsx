"use client"

import { Suspense, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useResendVerification, useVerifyOTP } from "@/hooks/use-api"
import { useAuthStore } from "@/stores/auth"
import { dashboardPath } from "@/lib/utils"
import { Shield, Loader2 } from "lucide-react"

function OtpFormContent() {
  const router = useRouter()
  const email = useSearchParams().get("email") || ""
  const { signIn, user } = useAuthStore()
  const verifyMutation = useVerifyOTP()
  const resend = useResendVerification()
  const [otp, setOtp] = useState("")

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    verifyMutation.mutate({ email, otp }, {
      onSuccess: (res) => {
        signIn(res.user, res.tokens)
        toast.success("Email verified!")
        router.push(dashboardPath(res.user.role))
      },
    })
  }

  return (
    <div className="rounded-2xl border border-white/5 bg-white/[0.03] p-8 shadow-2xl shadow-black/40 backdrop-blur-xl">
      <div className="mb-8 text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/10">
          <Shield className="h-6 w-6 text-emerald-400" />
        </div>
        <h1 className="text-2xl font-semibold tracking-tight text-white">Verify your email</h1>
        <p className="mt-2 text-sm text-white/50">
          Enter the 6-digit code sent to<br />
          <span className="font-medium text-white/70">{email || "your email"}</span>
        </p>
        <p className="mt-2 text-xs text-white/40">Running locally? The code is printed in the Django server console.</p>
      </div>

      <form onSubmit={onSubmit}>
        <Input
          aria-label="Verification code"
          value={otp}
          onChange={(e) => setOtp(e.target.value.replace(/\D/g, "").slice(0, 6))}
          inputMode="numeric"
          autoComplete="one-time-code"
          placeholder="000000"
          className="h-14 border-white/10 bg-white/5 text-center text-2xl tracking-[0.5em] text-white focus:border-emerald-500/50 focus:ring-emerald-500/20"
        />
        <Button
          type="submit"
          disabled={otp.length !== 6 || !email || verifyMutation.isPending}
          className="mt-6 h-11 w-full bg-gradient-to-r from-emerald-500 to-emerald-600 font-medium text-white shadow-lg shadow-emerald-500/20 hover:from-emerald-400 hover:to-emerald-500 transition-all duration-200"
        >
          {verifyMutation.isPending ? (
            <span className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Verifying...
            </span>
          ) : (
            "Verify Code"
          )}
        </Button>
      </form>

      <div className="mt-6 flex items-center justify-between text-sm">
        <button
          type="button"
          disabled={!email || resend.isPending}
          onClick={() => resend.mutate(email, { onSuccess: () => toast.success("A new code has been sent") })}
          className="text-emerald-400 hover:text-emerald-300 disabled:opacity-50"
        >
          Resend code
        </button>
        {user && (
          <button type="button" onClick={() => router.push(dashboardPath(user.role))} className="text-white/50 hover:text-white">
            Skip for now
          </button>
        )}
      </div>
    </div>
  )
}

export default function OtpPage() {
  return (
    <Suspense fallback={null}>
      <OtpFormContent />
    </Suspense>
  )
}
