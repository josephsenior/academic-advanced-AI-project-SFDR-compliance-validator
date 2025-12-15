"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import useSWR from "swr"
import { toast } from "sonner"
import { Shield, ArrowRight, Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"
import { UploadZone } from "@/components/upload-zone"
import { MetadataForm } from "@/components/metadata-form"
import { RecentValidations } from "@/components/recent-validations"
import { uploadDocument, validateDocument, listDocuments, deleteDocument } from "@/lib/api"
import type { DocumentMetadata, Document } from "@/lib/types"

interface UploadFile {
  file: File
  progress: number
  status: "pending" | "uploading" | "complete" | "error"
}

export default function UploadPage() {
  const router = useRouter()
  const { theme, setTheme } = useTheme()
  const [files, setFiles] = useState<UploadFile[]>([])
  const [metadata, setMetadata] = useState<DocumentMetadata>({
    client_type: "non-professional",
  })
  const [isValidating, setIsValidating] = useState(false)

  const { data: documents = [], mutate: refreshDocuments } = useSWR<Document[]>("documents", listDocuments, {
    fallbackData: [],
    onError: () => {
      // Silent fail for demo mode
    },
  })

  const handleFilesSelected = (newFiles: File[]) => {
    const uploadFiles: UploadFile[] = newFiles.map((file) => ({
      file,
      progress: 0,
      status: "pending",
    }))
    setFiles((prev) => [...prev, ...uploadFiles])
  }

  const handleRemoveFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const handleStartValidation = async () => {
    if (files.length === 0) {
      toast.error("Please select at least one file")
      return
    }

    setIsValidating(true)

    try {
      // Upload all files
      for (let i = 0; i < files.length; i++) {
        setFiles((prev) => prev.map((f, idx) => (idx === i ? { ...f, status: "uploading" } : f)))

        // Simulate progress
        for (let progress = 0; progress <= 100; progress += 10) {
          await new Promise((r) => setTimeout(r, 50))
          setFiles((prev) => prev.map((f, idx) => (idx === i ? { ...f, progress } : f)))
        }

        const result = await uploadDocument(files[i].file, metadata)

        setFiles((prev) => prev.map((f, idx) => (idx === i ? { ...f, status: "complete" } : f)))

        // Start validation and navigate
        await validateDocument(result.document_id)
        toast.success("Document uploaded successfully")
        router.push(`/dashboard/${result.document_id}`)
        return
      }
    } catch (error) {
      toast.error("Failed to upload document. Running in demo mode.")
      // Demo mode - navigate to demo dashboard
      router.push("/dashboard/demo-123")
    } finally {
      setIsValidating(false)
    }
  }

  const handleDeleteDocument = async (id: string) => {
    try {
      await deleteDocument(id)
      refreshDocuments()
      toast.success("Document deleted")
    } catch {
      toast.error("Failed to delete document")
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <Shield className="h-6 w-6 text-primary" />
            </div>
            <span className="font-semibold text-lg text-foreground">Compliance Validator</span>
          </div>
          <Button variant="ghost" size="icon" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
            <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          </Button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-12">
        {/* Hero */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4 text-foreground text-balance">Document Compliance Validator</h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto text-pretty">
            Upload your financial documents for automated compliance validation. Get instant feedback on ESG compliance,
            performance rules, and regulatory requirements.
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Upload Section */}
          <div className="lg:col-span-2 space-y-6">
            <UploadZone
              onFilesSelected={handleFilesSelected}
              files={files}
              onRemoveFile={handleRemoveFile}
              disabled={isValidating}
            />

            <MetadataForm metadata={metadata} onChange={setMetadata} />

            <Button
              size="lg"
              className="w-full gap-2"
              onClick={handleStartValidation}
              disabled={files.length === 0 || isValidating}
            >
              {isValidating ? (
                "Processing..."
              ) : (
                <>
                  Start Validation
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </Button>
          </div>

          {/* Recent Validations */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-foreground">Recent Validations</h2>
            <RecentValidations documents={documents} onDelete={handleDeleteDocument} />
          </div>
        </div>
      </main>
    </div>
  )
}
