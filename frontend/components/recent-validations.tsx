"use client"

import { formatDistanceToNow } from "date-fns"
import { FileText, ChevronRight, Trash2 } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import type { Document } from "@/lib/types"

interface RecentValidationsProps {
  documents: Document[]
  onDelete?: (id: string) => void
}

const statusColors: Record<string, string> = {
  complete: "bg-success/20 text-success border-success/30",
  error: "bg-destructive/20 text-destructive border-destructive/30",
  validating: "bg-primary/20 text-primary border-primary/30",
  pending: "bg-muted text-muted-foreground border-border",
}

export function RecentValidations({ documents, onDelete }: RecentValidationsProps) {
  if (documents.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p>No recent validations</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {documents.map((doc) => (
        <div
          key={doc.document_id}
          className="group flex items-center gap-4 p-4 rounded-lg bg-card border border-border hover:border-primary/30 transition-colors"
        >
          <div className="p-2 rounded-lg bg-primary/10">
            <FileText className="h-5 w-5 text-primary" />
          </div>

          <div className="flex-1 min-w-0">
            <p className="font-medium truncate text-foreground">{doc.filename}</p>
            <p className="text-sm text-muted-foreground">
              {formatDistanceToNow(new Date(doc.upload_date), { addSuffix: true })}
            </p>
          </div>

          <Badge variant="outline" className={statusColors[doc.status] || statusColors.pending}>
            {doc.status}
          </Badge>

          <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            {onDelete && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-muted-foreground hover:text-destructive"
                onClick={() => onDelete(doc.document_id)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
            <Link href={`/dashboard/${doc.document_id}`}>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <ChevronRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      ))}
    </div>
  )
}
