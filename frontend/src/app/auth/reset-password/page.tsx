"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useResetPassword } from "@/hooks/use-api"
import { Mail, KeyRound, Lock, Loader2, ArrowLeft } from "lucide-react"

const resetSchema = z.object({
  email: z.string().email("Invalid email"),
  otp: z.string().length(6, "Code must be 6 digits"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  confirmPassword: z.string()
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
})

type ResetForm = z.infer<typeof resetSchema>

export default function ResetPasswordPage() {
  const router = useRouter()
  const resetPassword = useResetPassword()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetForm>({ resolver: zodResolver(resetSchema) })

  const onSubmit = async (data: ResetForm) => {
    try {
      await resetPassword.mutateAsync({
        email: data.email,
        otp: data.otp,
        password: data.password,
      })
      toast.success("Password reset successfully. You can now sign in.")
      router.push("/auth/login")
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || err.message || "Invalid or expired reset code"
      toast.error(msg)
    }
  }

  return (
    <div className="rounded-2xl border border-white/5 bg-white/[0.03] p-8 shadow-2xl shadow-black/40 backdrop-blur-xl">
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-semibold tracking-tight text-white">Reset password</h1>
        <p className="mt-2 text-sm text-white/50">Enter your reset code and new password</p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        <div className="space-y-2">
          <label className="text-sm font-medium text-white/70">Email</label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
            <Input {...register("email")} type="email" placeholder="you@example.com" autoComplete="email" className="h-11 border-white/10 bg-white/5 pl-10 text-white placeholder:text-white/25 focus:border-emerald-500/50 focus:ring-emerald-500/20" />
          </div>
          {errors.email && <p className="text-xs text-red-400">{errors.email.message}</p>}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-white/70">Reset Code</label>
          <div className="relative">
            <KeyRound className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
            <Input {...register("otp")} type="text" placeholder="6-digit code" maxLength={6} className="h-11 border-white/10 bg-white/5 pl-10 text-white placeholder:text-white/25 focus:border-emerald-500/50 focus:ring-emerald-500/20 tracking-widest" />
          </div>
          {errors.otp && <p className="text-xs text-red-400">{errors.otp.message}</p>}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-white/70">New Password</label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
            <Input {...register("password")} type="password" placeholder="••••••••" autoComplete="new-password" className="h-11 border-white/10 bg-white/5 pl-10 text-white placeholder:text-white/25 focus:border-emerald-500/50 focus:ring-emerald-500/20" />
          </div>
          {errors.password && <p className="text-xs text-red-400">{errors.password.message}</p>}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-white/70">Confirm Password</label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
            <Input {...register("confirmPassword")} type="password" placeholder="••••••••" autoComplete="new-password" className="h-11 border-white/10 bg-white/5 pl-10 text-white placeholder:text-white/25 focus:border-emerald-500/50 focus:ring-emerald-500/20" />
          </div>
          {errors.confirmPassword && <p className="text-xs text-red-400">{errors.confirmPassword.message}</p>}
        </div>

        <Button type="submit" disabled={resetPassword.isPending} className="h-11 w-full bg-gradient-to-r from-emerald-500 to-emerald-600 font-medium text-white shadow-lg shadow-emerald-500/20 hover:from-emerald-400 hover:to-emerald-500 transition-all duration-200">
          {resetPassword.isPending ? (
            <span className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Resetting...
            </span>
          ) : (
            "Reset Password"
          )}
        </Button>
      </form>

      <div className="mt-6 text-center">
        <Link href="/auth/login" className="text-sm text-white/40 hover:text-emerald-400 transition-colors">
          <ArrowLeft className="mr-1 inline h-3 w-3" />
          Back to Sign In
        </Link>
      </div>
    </div>
  )
}
