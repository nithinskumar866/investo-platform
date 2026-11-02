"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useForgotPassword } from "@/hooks/use-api"
import { Mail, Loader2, ArrowLeft } from "lucide-react"

const forgotSchema = z.object({
  email: z.string().email("Invalid email"),
})

type ForgotForm = z.infer<typeof forgotSchema>

export default function ForgotPasswordPage() {
  const router = useRouter()
  const forgot = useForgotPassword()
  const loading = forgot.isPending

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotForm>({ resolver: zodResolver(forgotSchema) })

  const onSubmit = (data: ForgotForm) => {
    forgot.mutate(data.email, {
      onSuccess: () => {
        toast.success("If the account exists, a reset code has been sent")
        router.push(`/auth/reset-password?email=${encodeURIComponent(data.email)}`)
      },
    })
  }

  return (
    <div className="rounded-2xl border border-white/5 bg-white/[0.03] p-8 shadow-2xl shadow-black/40 backdrop-blur-xl">
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-semibold tracking-tight text-white">Forgot password?</h1>
        <p className="mt-2 text-sm text-white/50">Enter your email and we&apos;ll send you a 6-digit reset code</p>
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

        <Button type="submit" disabled={loading} className="h-11 w-full bg-gradient-to-r from-emerald-500 to-emerald-600 font-medium text-white shadow-lg shadow-emerald-500/20 hover:from-emerald-400 hover:to-emerald-500 transition-all duration-200">
          {loading ? (
            <span className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Sending...
            </span>
          ) : (
            "Send Reset Code"
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
