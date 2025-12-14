"use client"

import { useState } from "react"
import { Upload, FileText, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"

interface UploadZoneProps {
  onFilesSelected: (files: { document?: File; metadata?: File; prospectus?: File }) => void
  disabled?: boolean
}

export function UploadZone({ onFilesSelected, disabled }: UploadZoneProps) {
  const [documentFile, setDocumentFile] = useState<File | null>(null)
  const [metadataFile, setMetadataFile] = useState<File | null>(null)
  const [prospectusFile, setProspectusFile] = useState<File | null>(null)

  const handleDocumentChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setDocumentFile(file)
      onFilesSelected({ document: file, metadata: metadataFile || undefined, prospectus: prospectusFile || undefined })
    }
  }

  const handleMetadataChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setMetadataFile(file)
      onFilesSelected({ document: documentFile || undefined, metadata: file, prospectus: prospectusFile || undefined })
    }
  }

  const handleProspectusChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setProspectusFile(file)
      onFilesSelected({ document: documentFile || undefined, metadata: metadataFile || undefined, prospectus: file })
    }
  }

  const removeDocument = () => {
    setDocumentFile(null)
    onFilesSelected({ metadata: metadataFile || undefined, prospectus: prospectusFile || undefined })
  }

  const removeMetadata = () => {
    setMetadataFile(null)
    onFilesSelected({ document: documentFile || undefined, prospectus: prospectusFile || undefined })
  }

  const removeProspectus = () => {
    setProspectusFile(null)
    onFilesSelected({ document: documentFile || undefined, metadata: metadataFile || undefined })
  }

  return (
    <div className="space-y-6">
      {/* Document Upload */}
      <div className="space-y-2">
        <Label htmlFor="document" className="text-base font-medium">
          Document <span className="text-destructive">*</span>
        </Label>
        <div className={cn(
          "relative border-2 border-dashed rounded-xl p-8 text-center transition-all",
          documentFile ? "border-primary bg-primary/5" : "border-border hover:border-primary/50 hover:bg-accent/50",
          disabled && "opacity-50 cursor-not-allowed"
        )}>
          {!documentFile ? (
            <>
              <Input
                id="document"
                type="file"
                accept=".pptx,.pdf,.docx"
                onChange={handleDocumentChange}
                disabled={disabled}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <div className="flex flex-col items-center gap-3">
                <div className="p-3 rounded-full bg-primary/10">
                  <Upload className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="font-medium text-foreground">Upload Main Document</p>
                  <p className="text-sm text-muted-foreground">.pptx, .pdf, or .docx</p>
                </div>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-primary" />
                <span className="text-sm font-medium">{documentFile.name}</span>
              </div>
              <Button variant="ghost" size="icon" onClick={removeDocument} disabled={disabled}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Metadata Upload */}
      <div className="space-y-2">
        <Label htmlFor="metadata" className="text-base font-medium">
          Metadata <span className="text-muted-foreground text-sm">(Optional)</span>
        </Label>
        <div className={cn(
          "relative border-2 border-dashed rounded-xl p-6 text-center transition-all",
          metadataFile ? "border-primary bg-primary/5" : "border-border hover:border-primary/50 hover:bg-accent/50",
          disabled && "opacity-50 cursor-not-allowed"
        )}>
          {!metadataFile ? (
            <>
              <Input
                id="metadata"
                type="file"
                accept=".json"
                onChange={handleMetadataChange}
                disabled={disabled}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <div className="flex flex-col items-center gap-2">
                <FileText className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium text-foreground">Upload metadata.json</p>
                  <p className="text-xs text-muted-foreground">Optional - will be auto-detected if not provided</p>
                </div>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-primary" />
                <span className="text-sm font-medium">{metadataFile.name}</span>
              </div>
              <Button variant="ghost" size="icon" onClick={removeMetadata} disabled={disabled}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Prospectus Upload */}
      <div className="space-y-2">
        <Label htmlFor="prospectus" className="text-base font-medium">
          Prospectus <span className="text-muted-foreground text-sm">(Optional)</span>
        </Label>
        <div className={cn(
          "relative border-2 border-dashed rounded-xl p-6 text-center transition-all",
          prospectusFile ? "border-primary bg-primary/5" : "border-border hover:border-primary/50 hover:bg-accent/50",
          disabled && "opacity-50 cursor-not-allowed"
        )}>
          {!prospectusFile ? (
            <>
              <Input
                id="prospectus"
                type="file"
                accept=".pdf,.pptx,.docx"
                onChange={handleProspectusChange}
                disabled={disabled}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <div className="flex flex-col items-center gap-2">
                <FileText className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium text-foreground">Upload Prospectus</p>
                  <p className="text-xs text-muted-foreground">Optional - enables performance data validation</p>
                </div>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-primary" />
                <span className="text-sm font-medium">{prospectusFile.name}</span>
              </div>
              <Button variant="ghost" size="icon" onClick={removeProspectus} disabled={disabled}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
