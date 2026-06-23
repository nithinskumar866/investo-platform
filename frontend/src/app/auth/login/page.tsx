"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useLogin } from "@/hooks/use-api"
import { useAuthStore } from "@/stores/auth"
import { api } from "@/services/api"
import { Mail, Lock, Eye, EyeOff, Loader2 } from "lucide-react"

const loginSchema = z.object({
  email: z.string().email("Invalid email"),
  password: z.string().min(1, "Password is required"),
})

type LoginForm = z.infer<typeof loginSchema>

export default function LoginPage() {
  const router = useRouter()
  const setUser = useAuthStore((s) => s.setUser)
  const loginMutation = useLogin()
  const [showOtp, setShowOtp] = useState(false)
  const [loginEmail, setLoginEmail] = useState("")
  const [showPassword, setShowPassword] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) })

  const onSubmit = (data: LoginForm) => {
    loginMutation.mutate(data, {
      onSuccess: (res) => {
        api.setToken(res.tokens.access)
        localStorage.setItem("refresh_token", res.tokens.refresh)
        setUser(res.user)
        toast.success("Welcome back!")
        if (res.user.role === "entrepreneur") router.push("/founder")
        else if (res.user.role === "investor") router.push("/investor")
        else if (res.user.role === "admin") router.push("/admin")
        else router.push("/auth/login")
      },
      onError: (err: Error) => {
        if (err.message.toLowerCase().includes("otp") || err.message.toLowerCase().includes("verify")) {
          setLoginEmail(data.email)
          setShowOtp(true)
        }
        toast.error(err.message)
      },
    })
  }

  if (showOtp) {
    router.push(`/auth/otp?email=${encodeURIComponent(loginEmail)}`)
    return null
  }

  return (
    <div className="rounded-2xl border border-white/5 bg-white/[0.03] p-8 shadow-2xl shadow-black/40 backdrop-blur-xl">
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-semibold tracking-tight text-white">Welcome back</h1>
        <p className="mt-2 text-sm text-white/50">Sign in to your Investo account</p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        <div className="space-y-2">
          <label className="text-sm font-medium text-white/70">Email</label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
            <Input
              {...register("email")}
              type="email"
              placeholder="you@example.com"
              autoComplete="email"
              className="h-11 border-white/10 bg-white/5 pl-10 text-white placeholder:text-white/25 focus:border-emerald-500/50 focus:ring-emerald-500/20"
            />
          </div>
          {errors.email && <p className="text-xs text-red-400">{errors.email.message}</p>}
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-white/70">Password</label>
            <Link href="/auth/forgot-password" className="text-xs text-emerald-400/70 hover:text-emerald-400 transition-colors">
              Forgot?
            </Link>
          </div>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
            <Input
              {...register("password")}
              type={showPassword ? "text" : "password"}
              placeholder="Enter your password"
              autoComplete="current-password"
              className="h-11 border-white/10 bg-white/5 pl-10 pr-10 text-white placeholder:text-white/25 focus:border-emerald-500/50 focus:ring-emerald-500/20"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/50 transition-colors"
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.password && <p className="text-xs text-red-400">{errors.password.message}</p>}
        </div>

        <Button
          type="submit"
          disabled={loginMutation.isPending}
          className="h-11 w-full bg-gradient-to-r from-emerald-500 to-emerald-600 font-medium text-white shadow-lg shadow-emerald-500/20 hover:from-emerald-400 hover:to-emerald-500 hover:shadow-emerald-500/30 transition-all duration-200"
        >
          {loginMutation.isPending ? (
            <span className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Signing in...
            </span>
          ) : (
            "Sign In"
          )}
        </Button>
      </form>

      <div className="mt-8 text-center">
        <p className="text-sm text-white/40">
          Don&apos;t have an account?{" "}
          <Link href="/auth/register" className="font-medium text-emerald-400 hover:text-emerald-300 transition-colors">
            Create one
          </Link>
        </p>
      </div>

      <div className="mt-6 rounded-lg border border-white/5 bg-white/[0.02] p-3">
        <p className="text-center text-xs text-white/25">
          Demo: founder@investo.com / founder123
        </p>
      </div>
    </div>
  )
}
