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
  status: "pending" | "uploading" | "complete" | "error"
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
          "relative border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all duration-200",
          isDragActive ? "border-primary bg-primary/5" : "border-border hover:border-primary/50 hover:bg-accent/50",
          disabled && "opacity-50 cursor-not-allowed",
        )}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-4">
          <div className="p-4 rounded-full bg-primary/10">
            <Upload className="h-8 w-8 text-primary" />
          </div>
          <div>
            <p className="text-lg font-medium text-foreground">Drop your documents here</p>
            <p className="text-sm text-muted-foreground mt-1">or click to browse. Supports .pptx, .pdf, .docx</p>
          </div>
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
                {uploadFile.status === "complete" && <span className="text-xs text-success font-medium">Complete</span>}
                {uploadFile.status === "error" && <span className="text-xs text-destructive font-medium">Error</span>}
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
