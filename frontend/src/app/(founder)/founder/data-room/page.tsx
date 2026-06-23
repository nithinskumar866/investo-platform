"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { FileText, Download, Eye, Upload, FolderOpen, FileSpreadsheet, FileImage, File as FileIcon } from "lucide-react"
import { formatDate, formatRelativeTime } from "@/lib/utils"

type Document = {
  id: number
  title: string
  documentType: string
  fileSize: number
  status: "approved" | "pending" | "rejected"
  uploadedAt: string
}

const documents: Document[] = [
  { id: 1, title: "Pitch Deck v3", documentType: "application/pdf", fileSize: 4_200_000, status: "approved", uploadedAt: "2026-06-10T10:00:00Z" },
  { id: 2, title: "Financial Projections 2026", documentType: "application/vnd.ms-excel", fileSize: 1_800_000, status: "approved", uploadedAt: "2026-06-08T14:30:00Z" },
  { id: 3, title: "Cap Table Summary", documentType: "application/pdf", fileSize: 890_000, status: "approved", uploadedAt: "2026-06-05T09:15:00Z" },
  { id: 4, title: "IP Portfolio", documentType: "application/pdf", fileSize: 2_100_000, status: "pending", uploadedAt: "2026-06-12T16:45:00Z" },
  { id: 5, title: "Team Bios", documentType: "application/pdf", fileSize: 560_000, status: "approved", uploadedAt: "2026-06-01T11:00:00Z" },
  { id: 6, title: "Market Analysis Report", documentType: "application/pdf", fileSize: 3_400_000, status: "approved", uploadedAt: "2026-05-28T08:20:00Z" },
  { id: 7, title: "Product Roadmap Q3-Q4", documentType: "application/pdf", fileSize: 1_200_000, status: "pending", uploadedAt: "2026-06-14T13:00:00Z" },
  { id: 8, title: "Customer Testimonials", documentType: "image/png", fileSize: 15_200_000, status: "rejected", uploadedAt: "2026-06-07T15:30:00Z" },
]

function formatFileSize(bytes: number): string {
  if (bytes >= 1_000_000) return `${(bytes / 1_000_000).toFixed(1)} MB`
  if (bytes >= 1_000) return `${(bytes / 1_000).toFixed(0)} KB`
  return `${bytes} B`
}

function getFileIcon(type: string) {
  if (type.includes("spreadsheet") || type.includes("excel")) return FileSpreadsheet
  if (type.includes("image")) return FileImage
  if (type.includes("pdf")) return FileText
  return FileIcon
}

const statusVariant: Record<string, "success" | "warning" | "destructive"> = {
  approved: "success",
  pending: "warning",
  rejected: "destructive",
}

export default function DataRoomPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Data Room</h1>
          <p className="text-muted-foreground">Manage documents for investor due diligence</p>
        </div>
        <Button className="gap-2">
          <Upload className="h-4 w-4" /> Upload Document
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {documents.map((doc) => {
          const Icon = getFileIcon(doc.documentType)
          return (
            <Card key={doc.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <Icon className="h-5 w-5 text-primary" />
                  </div>
                  <Badge variant={statusVariant[doc.status]}>{doc.status}</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                <CardTitle className="text-sm leading-tight line-clamp-2">{doc.title}</CardTitle>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span>{formatFileSize(doc.fileSize)}</span>
                  <span>•</span>
                  <span>{formatRelativeTime(doc.uploadedAt)}</span>
                </div>
                <div className="flex gap-2 pt-2">
                  <Button size="sm" variant="outline" className="flex-1 gap-1">
                    <Eye className="h-3.5 w-3.5" /> View
                  </Button>
                  <Button size="sm" variant="outline" className="flex-1 gap-1">
                    <Download className="h-3.5 w-3.5" /> Download
                  </Button>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
