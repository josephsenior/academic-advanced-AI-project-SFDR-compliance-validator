"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import useSWR from "swr"
import { toast } from "sonner"
import { Shield, ArrowRight, Moon, Sun, FileText, FileCode, FileJson } from "lucide-react"
import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { UploadZone } from "@/components/upload-zone"
import { MetadataForm } from "@/components/metadata-form"
import { RecentValidations } from "@/components/recent-validations"
import { uploadDocument, validateDocument, listDocuments, deleteDocument } from "@/lib/api"
import type { DocumentMetadata, Document } from "@/lib/types"

interface UploadFile {
  file: File
  progress: number
  status: "pending" | "uploading" | "completed" | "error"
}

export default function UploadPage() {
  const router = useRouter()
  const { theme, setTheme } = useTheme()
  const [files, setFiles] = useState<UploadFile[]>([])
  const [metadata, setMetadata] = useState<DocumentMetadata>({
    is_professional_client: false,
  })
  const [rawMetadata, setRawMetadata] = useState<Record<string, any>>({})
  const [isValidating, setIsValidating] = useState(false)
  const [metadataFile, setMetadataFile] = useState<File | null>(null)
  const [prospectusFile, setProspectusFile] = useState<File | null>(null)

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

  const handleMetadataFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setMetadataFile(file)
    try {
      const text = await file.text()
      const json = JSON.parse(text)
      const normalized: DocumentMetadata = {
        societe_de_gestion: json["Société de Gestion"] || json.societe_de_gestion,
        is_sicav: json["Est ce que le produit fait partie de la Sicav luxembourgeoise "] ??
          json["Est ce que le produit fait partie de la Sicav d'Oddo"] ??
          json.is_sicav,
        is_professional_client: json["Le client est-il un professionnel"] ?? json.is_professional_client,
        is_new_strategy: json["Le document fait-il référence à une nouvelle Stratégie"] ?? json.is_new_strategy,
        is_new_product: json["Le document fait-il référence à un nouveau Produit"] ?? json.is_new_product,
      }
      setMetadata(normalized)
      toast.success("Metadata loaded from JSON and form auto-filled")
    } catch (err) {
      toast.error("Failed to parse metadata.json")
    }
  }

  const handleProspectusFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null
    setProspectusFile(file)
  }

  const handleStartValidation = async () => {
    if (files.length === 0) {
      toast.error("Please select at least one file")
      return
    }

    setIsValidating(true)

    try {
      // Only the first file is treated as the main document
      setFiles((prev) => prev.map((f, idx) => (idx === 0 ? { ...f, status: "uploading" } : f)))

      for (let progress = 0; progress <= 100; progress += 10) {
        await new Promise((r) => setTimeout(r, 50))
        setFiles((prev) => prev.map((f, idx) => (idx === 0 ? { ...f, progress } : f)))
      }

      // Merge raw metadata with current form values to preserve extra fields (like SICAV) while respecting user edits
      const finalMetadata = { ...rawMetadata, ...metadata }

      const result = await uploadDocument({
        document: files[0].file,
        metadata: finalMetadata,
        metadataFile: undefined, // Send as JSON object to preserve merges
        prospectusFile: prospectusFile ?? undefined,
      })

      setFiles((prev) => prev.map((f, idx) => (idx === 0 ? { ...f, status: "completed" } : f)))

      await validateDocument(result.document_id)
      toast.success("Document uploaded successfully")
      router.push(`/dashboard/${result.document_id}`)
      return
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
      <header className="border-b border-border bg-card/30 backdrop-blur-md sticky top-0 z-50 shadow-sm transition-all duration-300">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4 group">
            <div className="p-2 rounded-xl bg-primary/15 group-hover:bg-primary/25 transition-colors duration-300">
              <Shield className="h-6 w-6 text-primary" />
            </div>
            <div className="flex flex-col">
              <span className="font-bold text-lg tracking-tight text-foreground leading-none">ODDO BHF</span>
              <span className="text-[10px] font-bold uppercase tracking-widest text-primary/70">Compliance Validator</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              className="rounded-full hover:bg-primary/5"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            >
              <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
              <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-12">
        {/* Hero */}
        <div className="text-center mb-16 space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 mb-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
            </span>
            <span className="text-[10px] font-bold uppercase tracking-wider text-primary">AI-Powered Compliance</span>
          </div>
          <h1 className="text-5xl md:text-6xl font-black tracking-tighter text-foreground text-balance">
            Validator <span className="text-transparent bg-clip-text bg-linear-to-r from-primary to-primary/60">Intelligence</span>
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground/80 max-w-2xl mx-auto text-pretty font-medium italic">
            "Eliminate regulatory friction. Upload your financial documents for instantaneous, AI-driven compliance screening."
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

            <div className="grid md:grid-cols-2 gap-6 pb-6">
              <Card className="border-none bg-card/40 backdrop-blur-sm shadow-md group hover:shadow-lg transition-all duration-300">
                <CardHeader className="pb-3 border-b border-border/10">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-lg bg-primary/10 text-primary">
                      <FileCode className="h-4 w-4" />
                    </div>
                    <CardTitle className="text-sm font-bold uppercase tracking-widest text-muted-foreground/80">Metadata JSON</CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="pt-4 space-y-3">
                  <div className="relative">
                    <Input
                      type="file"
                      accept="application/json"
                      onChange={handleMetadataFile}
                      disabled={isValidating}
                      className="bg-background/50 border-border/50 file:bg-primary/10 file:text-primary file:border-none file:font-bold file:px-4 file:py-1 file:rounded-md file:mr-4 file:hover:bg-primary/20 transition-all"
                    />
                  </div>
                  <p className="text-[10px] font-medium text-muted-foreground/60 leading-tight">Optional: Automotive form population from JSON export.</p>
                  {metadataFile && (
                    <div className="flex items-center gap-2 p-2 rounded bg-primary/5 border border-primary/10">
                      <FileJson className="h-3 w-3 text-primary" />
                      <p className="text-[10px] font-bold text-primary truncate max-w-full italic">{metadataFile.name}</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card className="border-none bg-card/40 backdrop-blur-sm shadow-md group hover:shadow-lg transition-all duration-300">
                <CardHeader className="pb-3 border-b border-border/10">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-lg bg-primary/10 text-primary">
                      <FileText className="h-4 w-4" />
                    </div>
                    <CardTitle className="text-sm font-bold uppercase tracking-widest text-muted-foreground/80">Reference Data</CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="pt-4 space-y-3">
                  <div className="relative">
                    <Input
                      type="file"
                      accept=".pptx,.pdf,.docx,application/vnd.openxmlformats-officedocument.presentationml.presentation,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                      onChange={handleProspectusFile}
                      disabled={isValidating}
                      className="bg-background/50 border-border/50 file:bg-primary/10 file:text-primary file:border-none file:font-bold file:px-4 file:py-1 file:rounded-md file:mr-4 file:hover:bg-primary/20 transition-all"
                    />
                  </div>
                  <p className="text-[10px] font-medium text-muted-foreground/60 leading-tight">Optional: Prospectus or KID for numerical cross-checking.</p>
                  {prospectusFile && (
                    <div className="flex items-center gap-2 p-2 rounded bg-primary/5 border border-primary/10">
                      <Shield className="h-3 w-3 text-primary" />
                      <p className="text-[10px] font-bold text-primary truncate max-w-full italic">{prospectusFile.name}</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            <MetadataForm metadata={metadata} onChange={setMetadata} />

            <div className="pt-4">
              <Button
                size="lg"
                className="w-full h-14 gap-3 text-lg font-black tracking-tight uppercase shadow-xl hover:shadow-primary/20 hover:scale-[1.01] active:scale-[0.99] transition-all"
                onClick={handleStartValidation}
                disabled={files.length === 0 || isValidating}
              >
                {isValidating ? (
                  <>
                    <div className="h-5 w-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Processing Engine...
                  </>
                ) : (
                  <>
                    Validate Document Pool
                    <ArrowRight className="h-5 w-5" />
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Recent Validations Activity Feed */}
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold uppercase tracking-widest text-muted-foreground/80">Activity Stream</h2>
              <div className="h-px flex-1 bg-border/20 mx-4" />
            </div>
            <div className="rounded-2xl border border-border/10 bg-card/20 backdrop-blur-sm p-1">
              <RecentValidations documents={documents} onDelete={handleDeleteDocument} />
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
