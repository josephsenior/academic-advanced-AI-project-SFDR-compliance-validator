"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import useSWR from "swr"
import { toast } from "sonner"
import { Shield, ArrowRight, Moon, Sun, Upload, FileCheck, Sparkles, RefreshCw } from "lucide-react"
import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
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
    onError: (error) => {
      console.error("Failed to load documents:", error)
      toast.error("Unable to load recent validations")
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
      const errorMessage = error instanceof Error ? error.message : "Upload failed"
      console.error("Upload error:", error)
      toast.error(errorMessage)
    } finally {
      setIsValidating(false)
    }
  }

  const handleDeleteDocument = async (id: string) => {
    try {
      await deleteDocument(id)
      refreshDocuments()
      toast.success("Document deleted")
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to delete document"
      console.error("Delete error:", error)
      toast.error(errorMessage)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <Shield className="h-6 w-6 text-primary" />
            </div>
            <div>
              <span className="font-semibold text-lg text-foreground">Compliance Validator</span>
              <p className="text-xs text-muted-foreground">Financial Document Validation</p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
            <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          </Button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-12">
        {/* Hero Section with Cards */}
        <div className="mb-12">
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full text-sm font-medium mb-4">
              <Sparkles className="h-4 w-4" />
              AI-Powered Validation
            </div>
            <h1 className="text-5xl font-bold mb-4 text-foreground">
              Document Compliance Validator
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Upload your financial documents for automated compliance validation. Get instant feedback on ESG compliance,
              performance rules, and regulatory requirements.
            </p>
          </div>

          {/* Feature Cards */}
          <div className="grid md:grid-cols-3 gap-4 mb-8">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-blue-500/10">
                    <FileCheck className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold mb-1">Smart Analysis</h3>
                    <p className="text-sm text-muted-foreground">
                      AI-powered extraction and validation of financial data
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-green-500/10">
                    <Shield className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold mb-1">Compliance Check</h3>
                    <p className="text-sm text-muted-foreground">
                      Verify ESG, disclaimers, and regulatory requirements
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-purple-500/10">
                    <Upload className="h-5 w-5 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold mb-1">Instant Reports</h3>
                    <p className="text-sm text-muted-foreground">
                      Download detailed PDF reports in seconds
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Upload Section */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Upload Documents</CardTitle>
                <CardDescription>
                  Upload your main document and optional metadata/prospectus files
                </CardDescription>
              </CardHeader>
              <CardContent>
                <UploadZone
                  onFilesSelected={handleFilesSelected}
                  disabled={isValidating}
                />
              </CardContent>
            </Card>

            <Button
              size="lg"
              className="w-full gap-2"
              onClick={handleStartValidation}
              disabled={!documentFile || isValidating}
            >
              {isValidating ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  Processing...
                </>
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
            <Card>
              <CardHeader>
                <CardTitle>Recent Validations</CardTitle>
                <CardDescription>View your validation history</CardDescription>
              </CardHeader>
              <CardContent>
                <RecentValidations documents={documents} onDelete={handleDeleteDocument} />
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  )
}
