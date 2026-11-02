"use client"

import { useRef, useState } from "react"
import { toast } from "sonner"
import { Download, Loader2, Trash2, Upload } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Field } from "@/components/ui/field"
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useDeleteStartupDocument, useStartupDocuments, useUploadStartupDocument } from "@/hooks/use-api"
import { STARTUP_DOCUMENT_TYPES, humanize } from "@/lib/constants"
import { formatDate } from "@/lib/utils"
import { mediaUrl } from "@/services/api"

/** Owner-only documents attached to the startup itself (distinct from data rooms). */
export function StartupDocuments({ startupId }: { startupId: number }) {
  const { data: docs, isLoading } = useStartupDocuments(startupId)
  const upload = useUploadStartupDocument(startupId)
  const remove = useDeleteStartupDocument(startupId)
  const [name, setName] = useState("")
  const [type, setType] = useState("other")
  const [file, setFile] = useState<File | null>(null)
  const fileInput = useRef<HTMLInputElement>(null)

  const submit = () => {
    if (!file) return
    const form = new FormData()
    form.append("name", name.trim() || file.name)
    form.append("document_type", type)
    form.append("file", file)
    upload.mutate(form, {
      onSuccess: () => {
        toast.success("Document uploaded")
        setName("")
        setFile(null)
        if (fileInput.current) fileInput.current.value = ""
      },
    })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Documents</CardTitle>
        <CardDescription>Private to you. To share files with investors, use the Data Room.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-3">
          <Field label="Document name"><Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Defaults to file name" /></Field>
          <Field label="Type"><Select value={type} onChange={(e) => setType(e.target.value)} options={STARTUP_DOCUMENT_TYPES} /></Field>
          <Field label="File" hint="PDF, Office, image, txt, csv or md. Up to 10 MB.">
            <Input ref={fileInput} type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          </Field>
        </div>
        <Button type="button" disabled={!file || upload.isPending} onClick={submit}>
          {upload.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Upload className="mr-2 h-4 w-4" />}
          Upload document
        </Button>

        {isLoading ? (
          <Skeleton className="h-12 w-full" />
        ) : !docs?.length ? (
          <p className="text-sm text-muted-foreground">No documents uploaded yet.</p>
        ) : (
          <ul className="divide-y rounded-lg border">
            {docs.map((d) => (
              <li key={d.id} className="flex items-center justify-between gap-2 p-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{d.name}</p>
                  <p className="text-xs capitalize text-muted-foreground">{humanize(d.document_type)} &middot; {formatDate(d.uploaded_at)}</p>
                </div>
                <div className="flex shrink-0 gap-1">
                  <Button variant="ghost" size="icon" asChild>
                    <a href={mediaUrl(d.file) ?? "#"} target="_blank" rel="noopener noreferrer" aria-label={`Download ${d.name}`}><Download className="h-4 w-4" /></a>
                  </Button>
                  <Button variant="ghost" size="icon" aria-label={`Delete ${d.name}`} disabled={remove.isPending}
                    onClick={() => { if (confirm(`Delete "${d.name}"?`)) remove.mutate(d.id) }}>
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
