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

export default function UploadPage() {
  const router = useRouter()
  const { theme, setTheme } = useTheme()
  const [documentFile, setDocumentFile] = useState<File | undefined>()
  const [metadataFile, setMetadataFile] = useState<File | undefined>()
  const [prospectusFile, setProspectusFile] = useState<File | undefined>()
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

  const handleFilesSelected = (files: { document?: File; metadata?: File; prospectus?: File }) => {
    if (files.document) setDocumentFile(files.document)
    if (files.metadata) setMetadataFile(files.metadata)
    if (files.prospectus) setProspectusFile(files.prospectus)
  }

  const handleStartValidation = async () => {
    if (!documentFile) {
      toast.error("Please upload the main document")
      return
    }

    setIsValidating(true)

    try {
      const result = await uploadDocument(documentFile, metadataFile, prospectusFile)

      // Show upload result info
      if (!result.has_metadata) {
        toast.info("No metadata provided - using default validation settings")
      }
      if (!result.has_prospectus) {
        toast.info("No prospectus provided - performance validation will be limited")
      }

      // Start validation and navigate
      await validateDocument(result.document_id)
      toast.success("Document uploaded successfully")
      router.push(`/dashboard/${result.document_id}`)
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
              disabled={isValidating}
            />

            <Button
              size="lg"
              className="w-full gap-2"
              onClick={handleStartValidation}
              disabled={!documentFile || isValidating}
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
