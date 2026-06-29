"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useCreateStartup } from "@/hooks/use-api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { toast } from "sonner"
import { Loader2 } from "lucide-react"

export default function NewStartupPage() {
  const router = useRouter()
  const createStartup = useCreateStartup()
  const [formData, setFormData] = useState({
    name: "",
    tagline: "",
    description: "",
    industry: "",
    stage: "",
    location: "",
    funding_goal: "",
    funding_status: "",
    team_size: "",
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.name || !formData.tagline) {
      toast.error("Name and tagline are required.")
      return
    }

    if (!formData.industry || !formData.stage) {
      toast.error("Industry and Stage are required.")
      return
    }

    const payload = {
      ...formData,
      status: "active",
      funding_goal: formData.funding_goal ? parseInt(formData.funding_goal, 10) : undefined,
      team_size: formData.team_size ? parseInt(formData.team_size, 10) : undefined,
    }

    createStartup.mutate(payload as any, {
      onSuccess: () => {
        toast.success("Startup created successfully!")
        router.push("/founder/startups")
      },
      onError: (err: any) => {
        let msg = "Failed to create startup"
        if (err.response?.data) {
          if (typeof err.response.data === 'object' && err.response.data.error?.message) {
              msg = err.response.data.error.message;
          } else if (typeof err.response.data === 'object') {
              msg = Object.entries(err.response.data)
                .map(([key, value]) => `${key}: ${value}`)
                .join(", ")
          }
        } else if (err.message) {
          msg = err.message
        }
        toast.error(msg)
      },
    })
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Create New Startup</h1>
        <p className="text-muted-foreground">Add your startup details to the platform.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Basic Information</CardTitle>
          <CardDescription>This information will be visible to investors.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Startup Name *</label>
              <Input name="name" value={formData.name} onChange={handleChange} placeholder="e.g. Acme Corp" required />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Tagline *</label>
              <Input name="tagline" value={formData.tagline} onChange={handleChange} placeholder="e.g. Revolutionizing the industry" required />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Description</label>
              <textarea 
                name="description" 
                value={formData.description || ""} 
                onChange={handleChange as any} 
                className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Industry *</label>
                <select 
                  name="industry" 
                  value={formData.industry} 
                  onChange={handleChange}
                  required
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option value="">Select Industry</option>
                  <option value="SaaS">SaaS</option>
                  <option value="Fintech">Fintech</option>
                  <option value="Healthtech">Healthtech</option>
                  <option value="ai_ml">AI / Machine Learning</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Stage *</label>
                <select 
                  name="stage" 
                  value={formData.stage} 
                  onChange={handleChange}
                  required
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option value="">Select Stage</option>
                  <option value="Idea">Idea</option>
                  <option value="pre_seed">Pre-seed</option>
                  <option value="Seed">Seed</option>
                  <option value="Series A">Series A</option>
                </select>
              </div>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Funding Status</label>
              <select 
                name="funding_status" 
                value={formData.funding_status || ""} 
                onChange={handleChange}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <option value="">Select Status</option>
                <option value="raising">Raising</option>
                <option value="closed">Closed</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Location</label>
              <Input name="location" value={formData.location} onChange={handleChange} placeholder="e.g. San Francisco, CA" />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Funding Goal ($)</label>
                <Input name="funding_goal" type="number" value={formData.funding_goal} onChange={handleChange} placeholder="e.g. 500000" />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Team Size</label>
                <Input name="team_size" type="number" value={formData.team_size} onChange={handleChange} placeholder="e.g. 5" />
              </div>
            </div>

            <div className="pt-4 flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => router.push("/founder/startups")}>
                Cancel
              </Button>
              <Button type="submit" disabled={createStartup.isPending}>
                {createStartup.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Create Startup
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
