"use client"

import { useRouter, useSearchParams } from "next/navigation"
import React, { useRef, type KeyboardEvent } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useVerifyOTP } from "@/hooks/use-api"
import { useAuthStore } from "@/stores/auth"
import { api } from "@/services/api"
import { Shield, Loader2 } from "lucide-react"

const otpSchema = z.object({
  otp0: z.string().length(1),
  otp1: z.string().length(1),
  otp2: z.string().length(1),
  otp3: z.string().length(1),
  otp4: z.string().length(1),
  otp5: z.string().length(1),
})

type OtpForm = z.infer<typeof otpSchema>

function OtpFormContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const email = searchParams.get("email") || ""
  const setUser = useAuthStore((s) => s.setUser)
  const verifyMutation = useVerifyOTP()
  const inputsRef = useRef<(HTMLInputElement | null)[]>([])

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<OtpForm>({ resolver: zodResolver(otpSchema) })

  const handleKeyDown = (index: number, e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace" && !(e.target as HTMLInputElement).value && index > 0) {
      inputsRef.current[index - 1]?.focus()
    }
  }

  const handleChange = (index: number, value: string) => {
    if (value && index < 5) {
      inputsRef.current[index + 1]?.focus()
    }
  }

  const onSubmit = (data: OtpForm) => {
    const otp = [data.otp0, data.otp1, data.otp2, data.otp3, data.otp4, data.otp5].join("")

    if (!email) {
      toast.error("No email provided")
      return
    }

    verifyMutation.mutate(
      { email, otp },
      {
        onSuccess: (res) => {
          api.setToken(res.tokens.access)
          localStorage.setItem("refresh_token", res.tokens.refresh)
          setUser(res.user)
          toast.success("Email verified!")
          if (res.user.role === "entrepreneur") router.push("/founder")
          else if (res.user.role === "investor") router.push("/investor")
          else router.push("/auth/login")
        },
        onError: (err: Error) => {
          toast.error(err.message)
        },
      },
    )
  }

  return (
    <div className="rounded-2xl border border-white/5 bg-white/[0.03] p-8 shadow-2xl shadow-black/40 backdrop-blur-xl">
      <div className="mb-8 text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/10">
          <Shield className="h-6 w-6 text-emerald-400" />
        </div>
        <h1 className="text-2xl font-semibold tracking-tight text-white">Verify OTP</h1>
        <p className="mt-2 text-sm text-white/50">
          Enter the 6-digit code sent to<br />
          <span className="font-medium text-white/70">{email || "your email"}</span>
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="flex justify-center gap-2">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <Input
              key={i}
              type="text"
              inputMode="numeric"
              maxLength={1}
              className="h-14 w-12 border-white/10 bg-white/5 text-center text-lg text-white focus:border-emerald-500/50 focus:ring-emerald-500/20"
              {...register(`otp${i}` as keyof OtpForm, {
                onChange: (e) => handleChange(i, e.target.value),
              })}
              onKeyDown={(e) => handleKeyDown(i, e)}
              ref={(el) => {
                inputsRef.current[i] = el
              }}
            />
          ))}
        </div>
        {Object.keys(errors).length > 0 && (
          <p className="mt-3 text-center text-xs text-red-400">Enter all 6 digits</p>
        )}

        <Button
          type="submit"
          disabled={verifyMutation.isPending}
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
    </div>
  )
}

export default function OtpPage() {
  return (
    <React.Suspense fallback={<div>Loading...</div>}>
      <OtpFormContent />
    </React.Suspense>
  )
}
