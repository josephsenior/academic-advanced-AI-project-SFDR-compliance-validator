"use client"

import { useCallback, useState } from "react"
import { useDropzone } from "react-dropzone"
import { Upload, FileText, X, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { Progress } from "@/components/ui/progress"
import { Button } from "@/components/ui/button"

interface UploadFile {
  file: File
  progress: number
  status: "pending" | "uploading" | "completed" | "error"
}

interface UploadZoneProps {
  onFilesSelected: (files: File[]) => void
  files: UploadFile[]
  onRemoveFile: (index: number) => void
  disabled?: boolean
}

export function UploadZone({ onFilesSelected, files, onRemoveFile, disabled }: UploadZoneProps) {
  const [isDragActive, setIsDragActive] = useState(false)

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      onFilesSelected(acceptedFiles)
    },
    [onFilesSelected],
  )

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    accept: {
      "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"],
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
    disabled,
    onDragEnter: () => setIsDragActive(true),
    onDragLeave: () => setIsDragActive(false),
  })

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={cn(
          "relative border-2 border-dashed rounded-2xl p-16 text-center cursor-pointer transition-all duration-500 overflow-hidden group",
          isDragActive
            ? "border-primary bg-primary/5 shadow-[inset_0_0_40px_rgba(var(--primary-rgb),0.1)] scale-[1.01]"
            : "border-border/60 hover:border-primary/40 hover:bg-primary/2 hover:shadow-lg",
          disabled && "opacity-50 cursor-not-allowed",
        )}
      >
        {/* Animated Background Pulse */}
        {isDragActive && (
          <div className="absolute inset-0 bg-primary/5 animate-pulse" />
        )}

        <input {...getInputProps()} />
        <div className="relative flex flex-col items-center gap-6">
          <div className={cn(
            "p-5 rounded-2xl bg-primary/10 transition-transform duration-500 group-hover:scale-110 group-hover:rotate-3",
            isDragActive && "scale-125 rotate-6 bg-primary/20"
          )}>
            <Upload className={cn(
              "h-10 w-10 text-primary transition-all duration-500",
              isDragActive && "animate-bounce"
            )} />
          </div>
          <div className="space-y-2">
            <p className="text-2xl font-black tracking-tight text-foreground uppercase">
              {isDragActive ? "Release to Analyze" : "Deposit Documents"}
            </p>
            <p className="text-sm font-medium text-muted-foreground/70 max-w-xs mx-auto">
              Securely drop your .pptx, .pdf, or .docx files here for instant AI verification.
            </p>
          </div>
          {!isDragActive && (
            <div className="mt-2 px-4 py-1.5 rounded-full border border-border/40 bg-background/50 text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60 shadow-sm">
              Standardized Ingestion Engine
            </div>
          )}
        </div>
      </div>
      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((uploadFile, index) => (
            <div key={index} className="flex items-center gap-3 p-3 rounded-lg bg-card border border-border">
              <FileText className="h-5 w-5 text-primary shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate text-foreground">{uploadFile.file.name}</p>
                {uploadFile.status === "uploading" && <Progress value={uploadFile.progress} className="h-1.5 mt-2" />}
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {uploadFile.status === "uploading" && <Loader2 className="h-4 w-4 animate-spin text-primary" />}
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => onRemoveFile(index)}
                  disabled={uploadFile.status === "uploading"}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

    </div>
  )
}
