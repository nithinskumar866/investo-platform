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
import { useRegister } from "@/hooks/use-api"
import { Mail, Lock, User, Users, Loader2, Briefcase, UserCheck } from "lucide-react"

const registerSchema = z.object({
  first_name: z.string().min(1, "First name is required"),
  last_name: z.string().min(1, "Last name is required"),
  email: z.string().email("Invalid email"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  confirm_password: z.string().min(8, "Please confirm your password"),
  role: z.enum(["entrepreneur", "investor"]),
}).refine((d) => d.password === d.confirm_password, {
  message: "Passwords do not match",
  path: ["confirm_password"],
})

type RegisterForm = z.infer<typeof registerSchema>

export default function RegisterPage() {
  const router = useRouter()
  const registerMutation = useRegister()
  const [selectedRole, setSelectedRole] = useState<"entrepreneur" | "investor">("entrepreneur")

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: { role: "entrepreneur" },
  })

  const onSubmit = (data: RegisterForm) => {
    const { confirm_password, ...payload } = data
    registerMutation.mutate({ ...payload, confirm_password }, {
      onSuccess: () => {
        toast.success("Account created! Please sign in.")
        router.push("/auth/login")
      },
      onError: (err: Error) => {
        toast.error(err.message)
      },
    })
  }

  return (
    <div className="rounded-2xl border border-white/5 bg-white/[0.03] p-8 shadow-2xl shadow-black/40 backdrop-blur-xl">
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-semibold tracking-tight text-white">Create your account</h1>
        <p className="mt-2 text-sm text-white/50">Join the venture ecosystem</p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-white/70">First name</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
              <Input {...register("first_name")} placeholder="John" autoComplete="given-name" className="h-11 border-white/10 bg-white/5 pl-10 text-white placeholder:text-white/25 focus:border-emerald-500/50 focus:ring-emerald-500/20" />
            </div>
            {errors.first_name && <p className="text-xs text-red-400">{errors.first_name.message}</p>}
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-white/70">Last name</label>
            <div className="relative">
              <Users className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
              <Input {...register("last_name")} placeholder="Doe" autoComplete="family-name" className="h-11 border-white/10 bg-white/5 pl-10 text-white placeholder:text-white/25 focus:border-emerald-500/50 focus:ring-emerald-500/20" />
            </div>
            {errors.last_name && <p className="text-xs text-red-400">{errors.last_name.message}</p>}
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-white/70">Email</label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
            <Input {...register("email")} type="email" placeholder="you@example.com" autoComplete="email" className="h-11 border-white/10 bg-white/5 pl-10 text-white placeholder:text-white/25 focus:border-emerald-500/50 focus:ring-emerald-500/20" />
          </div>
          {errors.email && <p className="text-xs text-red-400">{errors.email.message}</p>}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-white/70">Password</label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
            <Input {...register("password")} type="password" placeholder="Min. 8 characters" autoComplete="new-password" className="h-11 border-white/10 bg-white/5 pl-10 text-white placeholder:text-white/25 focus:border-emerald-500/50 focus:ring-emerald-500/20" />
          </div>
          {errors.password && <p className="text-xs text-red-400">{errors.password.message}</p>}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-white/70">Confirm password</label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
            <Input {...register("confirm_password")} type="password" placeholder="Confirm your password" autoComplete="new-password" className="h-11 border-white/10 bg-white/5 pl-10 text-white placeholder:text-white/25 focus:border-emerald-500/50 focus:ring-emerald-500/20" />
          </div>
          {errors.confirm_password && <p className="text-xs text-red-400">{errors.confirm_password.message}</p>}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-white/70">I am a...</label>
          <div className="grid grid-cols-2 gap-3">
            {(["entrepreneur", "investor"] as const).map((role) => (
              <button
                key={role}
                type="button"
                onClick={() => { setSelectedRole(role); setValue("role", role) }}
                className={`flex cursor-pointer flex-col items-center gap-2 rounded-xl border p-4 transition-all ${
                  selectedRole === role
                    ? "border-emerald-500/50 bg-emerald-500/10"
                    : "border-white/10 bg-white/5 hover:border-white/20"
                }`}
              >
                {role === "entrepreneur" ? (
                  <Briefcase className="h-6 w-6 text-emerald-400" />
                ) : (
                  <UserCheck className="h-6 w-6 text-emerald-400" />
                )}
                <span className="text-sm font-medium text-white/80 capitalize">{role}</span>
                <span className="text-xs text-white/40">
                  {role === "entrepreneur" ? "I have a startup" : "I want to invest"}
                </span>
              </button>
            ))}
            <input type="hidden" {...register("role")} />
          </div>
          {errors.role && <p className="text-xs text-red-400">{errors.role.message}</p>}
        </div>

        <Button
          type="submit"
          disabled={registerMutation.isPending}
          className="h-11 w-full bg-gradient-to-r from-emerald-500 to-emerald-600 font-medium text-white shadow-lg shadow-emerald-500/20 hover:from-emerald-400 hover:to-emerald-500 hover:shadow-emerald-500/30 transition-all duration-200"
        >
          {registerMutation.isPending ? (
            <span className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Creating account...
            </span>
          ) : (
            "Create Account"
          )}
        </Button>
      </form>

      <div className="mt-8 text-center">
        <p className="text-sm text-white/40">
          Already have an account?{" "}
          <Link href="/auth/login" className="font-medium text-emerald-400 hover:text-emerald-300 transition-colors">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
