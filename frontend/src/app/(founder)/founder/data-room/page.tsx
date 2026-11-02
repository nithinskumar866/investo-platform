"use client"

import { useEffect, useRef, useState } from "react"
import Link from "next/link"
import { toast } from "sonner"
import { Check, Download, FolderOpen, Loader2, Plus, Trash2, Upload, X } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Field } from "@/components/ui/field"
import { Skeleton } from "@/components/ui/skeleton"
import {
  useAccessRequests, useCreateDataRoom, useDataRoom, useDataRooms, useDecideAccessRequest,
  useDeleteDataRoom, useDeleteRoomDocument, useMyStartups, useUploadRoomDocument,
} from "@/hooks/use-api"
import { DATA_ROOM_DOCUMENT_TYPES, humanize } from "@/lib/constants"
import { cn, formatFileSize, formatRelativeTime } from "@/lib/utils"
import { mediaUrl } from "@/services/api"

function RoomDetail({ roomId }: { roomId: number }) {
  const { data: room, isLoading } = useDataRoom(roomId)
  const upload = useUploadRoomDocument(roomId)
  const removeDoc = useDeleteRoomDocument()
  const [title, setTitle] = useState("")
  const [type, setType] = useState("other")
  const [file, setFile] = useState<File | null>(null)
  const fileInput = useRef<HTMLInputElement>(null)

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return
    const form = new FormData()
    form.append("title", title.trim() || file.name)
    form.append("document_type", type)
    form.append("file", file)
    upload.mutate(form, {
      onSuccess: () => {
        toast.success("Document uploaded")
        setTitle("")
        setFile(null)
        if (fileInput.current) fileInput.current.value = ""
      },
    })
  }

  if (isLoading || !room) return <Skeleton className="h-64 w-full" />

  return (
    <Card>
      <CardHeader>
        <CardTitle>{room.title}</CardTitle>
        {room.description && <CardDescription>{room.description}</CardDescription>}
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={submit} className="space-y-3 rounded-lg border p-3">
          <div className="grid gap-3 sm:grid-cols-3">
            <Field label="Document title"><Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Defaults to file name" /></Field>
            <Field label="Document type"><Select value={type} onChange={(e) => setType(e.target.value)} options={DATA_ROOM_DOCUMENT_TYPES} /></Field>
            <Field label="File"><Input ref={fileInput} type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)} /></Field>
          </div>
          <Button type="submit" disabled={!file || upload.isPending}>
            {upload.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Upload className="mr-2 h-4 w-4" />}
            Upload document
          </Button>
        </form>

        {room.documents.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">No documents in this room yet.</p>
        ) : (
          <ul className="divide-y rounded-lg border" aria-label="Room documents">
            {room.documents.map((doc) => (
              <li key={doc.id} className="flex items-center justify-between gap-2 p-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{doc.title}</p>
                  <p className="text-xs capitalize text-muted-foreground">
                    {humanize(doc.document_type)} &middot; {formatFileSize(doc.file_size)} &middot; v{doc.version} &middot; {formatRelativeTime(doc.created_at)}
                  </p>
                </div>
                <div className="flex shrink-0 gap-1">
                  {doc.signed_url && (
                    <Button variant="ghost" size="icon" asChild>
                      <a href={mediaUrl(doc.signed_url) ?? "#"} target="_blank" rel="noopener noreferrer" aria-label={`Download ${doc.title}`}><Download className="h-4 w-4" /></a>
                    </Button>
                  )}
                  <Button variant="ghost" size="icon" aria-label={`Delete ${doc.title}`} disabled={removeDoc.isPending}
                    onClick={() => { if (confirm(`Delete "${doc.title}"?`)) removeDoc.mutate(doc.id) }}>
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

function AccessRequests() {
  const { data: requests, isLoading } = useAccessRequests()
  const decide = useDecideAccessRequest()

  return (
    <Card>
      <CardHeader>
        <CardTitle>Access requests</CardTitle>
        <CardDescription>Investors can only see a room&apos;s documents after you approve them.</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-16 w-full" />
        ) : !requests?.length ? (
          <p className="py-4 text-center text-sm text-muted-foreground">No access requests yet.</p>
        ) : (
          <ul className="divide-y" aria-label="Access requests">
            {requests.map((r) => (
              <li key={r.id} className="flex flex-wrap items-center justify-between gap-2 py-3" data-testid={`access-request-${r.id}`} data-room={r.data_room_title}>
                <div className="min-w-0">
                  <p className="text-sm font-medium">{r.investor_name}</p>
                  <p className="text-xs text-muted-foreground">{r.startup_name}: {r.data_room_title} &middot; {formatRelativeTime(r.created_at)}</p>
                  {r.message && <p className="mt-1 text-sm text-muted-foreground">&ldquo;{r.message}&rdquo;</p>}
                </div>
                {r.status === "pending" ? (
                  <div className="flex gap-2">
                    <Button size="sm" disabled={decide.isPending}
                      onClick={() => decide.mutate({ id: r.id, decision: "approve" }, { onSuccess: () => toast.success(`Access approved for ${r.investor_name}`) })}>
                      <Check className="mr-1 h-3 w-3" /> Approve
                    </Button>
                    <Button size="sm" variant="outline" disabled={decide.isPending}
                      onClick={() => decide.mutate({ id: r.id, decision: "deny" }, { onSuccess: () => toast.success("Request denied") })}>
                      <X className="mr-1 h-3 w-3" /> Deny
                    </Button>
                  </div>
                ) : (
                  <Badge variant={r.status === "approved" ? "success" : "destructive"}>{r.status}</Badge>
                )}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}

export default function DataRoomPage() {
  const { data: startups, isLoading: startupsLoading } = useMyStartups()
  const [startupId, setStartupId] = useState<number | undefined>()
  const [roomId, setRoomId] = useState<number | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const { data: rooms, isLoading: roomsLoading } = useDataRooms(startupId)
  const createRoom = useCreateDataRoom()
  const deleteRoom = useDeleteDataRoom()

  useEffect(() => {
    if (!startupId && startups?.length) setStartupId(startups[0].id)
  }, [startups, startupId])

  useEffect(() => {
    if (rooms && !rooms.some((r) => r.id === roomId)) setRoomId(rooms[0]?.id ?? null)
  }, [rooms, roomId])

  const submitRoom = (e: React.FormEvent) => {
    e.preventDefault()
    if (!startupId) return
    createRoom.mutate(
      { startup_id: startupId, title: title.trim(), description: description.trim() },
      {
        onSuccess: (room) => {
          toast.success("Data room created")
          setRoomId(room.id)
          setTitle("")
          setDescription("")
          setShowCreate(false)
        },
      },
    )
  }

  if (startupsLoading) return <Skeleton className="h-64 w-full" />

  if (!startups?.length) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold tracking-tight">Data Room</h1>
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-12 text-center text-muted-foreground">
            <FolderOpen className="h-10 w-10" />
            <p>Create a startup first, then add a data room for investor due diligence.</p>
            <Button asChild><Link href="/founder/startups/new">Create a startup</Link></Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Data Room</h1>
          <p className="text-muted-foreground">Share documents with approved investors</p>
        </div>
        <div className="flex items-end gap-2">
          <Field label="Startup">
            <Select className="w-56" value={startupId ?? ""} onChange={(e) => { setStartupId(Number(e.target.value)); setRoomId(null) }}
              options={startups.map((s) => ({ value: String(s.id), label: s.name }))} />
          </Field>
          <Button onClick={() => setShowCreate((v) => !v)}>
            <Plus className="mr-1 h-4 w-4" /> New room
          </Button>
        </div>
      </div>

      {showCreate && (
        <Card>
          <CardContent className="p-4">
            <form onSubmit={submitRoom} className="space-y-3">
              <Field label="Room title"><Input value={title} onChange={(e) => setTitle(e.target.value)} required /></Field>
              <Field label="Room description"><Textarea value={description} onChange={(e) => setDescription(e.target.value)} /></Field>
              <Button type="submit" disabled={createRoom.isPending}>
                {createRoom.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Create room
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-2">
          <h2 className="text-sm font-semibold">Rooms</h2>
          {roomsLoading ? (
            <Skeleton className="h-24 w-full" />
          ) : !rooms?.length ? (
            <p className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">No rooms for this startup yet.</p>
          ) : (
            rooms.map((room) => (
              <div key={room.id} className={cn("flex items-center gap-1 rounded-lg border p-1", roomId === room.id && "border-primary bg-accent/20")}>
                <button type="button" onClick={() => setRoomId(room.id)} className="min-w-0 flex-1 p-2 text-left">
                  <p className="truncate text-sm font-medium">{room.title}</p>
                  <p className="text-xs text-muted-foreground">{room.document_count} document{room.document_count === 1 ? "" : "s"}</p>
                </button>
                <Button variant="ghost" size="icon" aria-label={`Delete room ${room.title}`} disabled={deleteRoom.isPending}
                  onClick={() => { if (confirm(`Delete room "${room.title}" and its documents?`)) deleteRoom.mutate(room.id) }}>
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            ))
          )}
        </div>
        <div className="space-y-6 lg:col-span-2">
          {roomId && <RoomDetail key={roomId} roomId={roomId} />}
          <AccessRequests />
        </div>
      </div>
    </div>
  )
}
