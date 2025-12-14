"use client"

import { use, useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import useSWR from "swr"
import { toast } from "sonner"
import { ArrowLeft, Download, FileJson, Trash2, Search, Moon, Sun, PartyPopper, RefreshCw } from "lucide-react"
import { useTheme } from "next-themes"
import Link from "next/link"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

import { ComplianceScoreGauge } from "@/components/compliance-score-gauge"
import { StatusBadge } from "@/components/status-badge"
import { IssueCard } from "@/components/issue-card"
import { CategoryFilter } from "@/components/category-filter"
import { SeverityFilter } from "@/components/severity-filter"
import { StatisticsTable } from "@/components/statistics-table"
import { ProgressSteps } from "@/components/progress-steps"
import { Badge } from "@/components/ui/badge"

import { useUIStore } from "@/lib/store"
import {
  getValidationStatus,
  getValidationResults,
  applyFixes,
  downloadReport,
  deleteDocument,
} from "@/lib/api"
import { demoResults } from "@/lib/demo-data"
import type { ValidationResults, ValidationStatus, Issue, SortOption } from "@/lib/types"

const categoryColors: Record<string, string> = {
  esg: "#EF4444",
  performance: "#F59E0B",
  structure: "#3B82F6",
  disclaimers: "#EAB308",
  registration: "#8B5CF6",
  data_consistency: "#10B981",
  other: "#6B7280",
}

const categoryLabels: Record<string, string> = {
  esg: "ESG Compliance",
  performance: "Performance Rules",
  structure: "Structure Issues",
  disclaimers: "Disclaimers",
  registration: "Registration",
  data_consistency: "Data Consistency",
  other: "Other",
}

export default function DashboardPage({
  params,
}: {
  params: Promise<{ documentId: string }>
}) {
  const { documentId } = use(params)
  const router = useRouter()
  const { theme, setTheme } = useTheme()
  const [localIssues, setLocalIssues] = useState<Record<string, Issue>>({})
  const [isDownloading, setIsDownloading] = useState(false)

  const {
    selectedCategories,
    toggleCategory,
    selectedSeverities,
    toggleSeverity,
    searchQuery,
    setSearchQuery,
    sortOption,
    setSortOption,
    resetFilters,
  } = useUIStore()

  // Fetch validation status
  const { data: status } = useSWR<ValidationStatus>(`status-${documentId}`, () => getValidationStatus(documentId), {
    refreshInterval: (data) => (data?.status === "completed" || data?.status === "failed" ? 0 : 2000),
    onError: (error) => {
      console.error("Failed to fetch validation status:", error)
      toast.error("Unable to fetch validation status")
    },
  })

  // Fetch validation results
  const { data: results, mutate: refreshResults } = useSWR<ValidationResults>(
    status?.status === "completed" ? `results-${documentId}` : null,
    () => getValidationResults(documentId),
    {
      onError: (error) => {
        console.error("Failed to fetch validation results:", error)
        toast.error("Unable to fetch validation results")
      },
    },
  )

  // Reset filters on mount
  useEffect(() => {
    resetFilters()
  }, [resetFilters])

  // Flatten all issues
  const allIssues = useMemo(() => {
    if (!results) {
      console.log('[DEBUG] No results yet')
      return []
    }
    console.log('[DEBUG] Results received:', {
      total_issues: results.total_issues,
      has_compliance_issues: !!results.compliance_issues,
      compliance_issues_count: results.compliance_issues?.length,
      compliance_issues_sample: results.compliance_issues?.[0]
    })
    // Use compliance_issues array directly instead of flattening issues_by_category
    return results.compliance_issues || []
  }, [results])

  // Get issues with local state merged
  const issuesWithState = useMemo(() => {
    return allIssues.map((issue: Issue) => ({
      ...issue,
      ...localIssues[`${issue.issue_type}-${issue.location}`],
    }))
  }, [allIssues, localIssues])

  // Filter and sort issues
  const filteredIssues = useMemo(() => {
    let filtered = issuesWithState
    console.log('[DEBUG] Filtering:', {
      total_issues: issuesWithState.length,
      selectedCategories,
      selectedSeverities,
      searchQuery
    })

    // Filter by category
    if (selectedCategories.length > 0) {
      console.log('[DEBUG] Applying category filter')
      filtered = filtered.filter((issue: Issue) => selectedCategories.includes(issue.category))
    }

    // Filter by severity
    if (selectedSeverities.length > 0) {
      console.log('[DEBUG] Applying severity filter')
      filtered = filtered.filter((issue: Issue) => selectedSeverities.includes(issue.severity))
    }

    // Filter by search query
    if (searchQuery) {
      console.log('[DEBUG] Applying search filter')
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(
        (issue: Issue) =>
          issue.message.toLowerCase().includes(query) ||
          issue.category.toLowerCase().includes(query) ||
          issue.location.toLowerCase().includes(query),
      )
    }

    // Sort
    filtered.sort((a: Issue, b: Issue) => {
      if (sortOption === "severity") {
        const severityOrder: Record<string, number> = { error: 0, critical: 1, warning: 2, high: 3, medium: 4, low: 5 }
        return severityOrder[a.severity] - severityOrder[b.severity]
      }
      if (sortOption === "location") {
        return (a.slide_number || 0) - (b.slide_number || 0)
      }
      return 0
    })

    console.log('[DEBUG] Filtered result:', filtered.length)
    return filtered
  }, [issuesWithState, selectedCategories, selectedSeverities, searchQuery, sortOption])

  // Category counts for filter
  const categoryCounts = useMemo(() => {
    if (!results) return []
    return Object.entries(results.issues_by_category).map(([name, issues]) => ({
      name: categoryLabels[name] || name,
      count: issues.length,
      color: categoryColors[name] || "#6B7280",
    }))
  }, [results])

  const handleApplyFix = async (issue: Issue) => {
    try {
      await applyFixes(documentId)
      toast.success("Fix applied successfully")
      refreshResults()
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to apply fix"
      console.error("Apply fix error:", error)
      toast.error(errorMessage)
    }
  }

  const handleMarkReviewed = (issue: Issue) => {
    const key = `${issue.issue_type}-${issue.location}`
    setLocalIssues((prev) => ({
      ...prev,
      [key]: { ...issue, reviewed: true },
    }))
    toast.success("Marked as reviewed")
  }

  const handleIgnore = (issue: Issue) => {
    const key = `${issue.issue_type}-${issue.location}`
    setLocalIssues((prev) => ({
      ...prev,
      [key]: { ...issue, ignored: true },
    }))
    toast.success("Issue ignored")
  }

  const handleDownload = async () => {
    // Download a detailed validation report (PDF) from the backend
    setIsDownloading(true)
    try {
      const blob = await downloadReport(documentId, 'pdf')
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `validation_report_${documentId}.pdf`
      a.click()
      URL.revokeObjectURL(url)
      toast.success("PDF report downloaded")
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to download report"
      console.error("Download report error:", error)
      toast.error(errorMessage)
    } finally {
      setIsDownloading(false)
    }
  }

  const handleExportJSON = () => {
    try {
      const data = JSON.stringify(results, null, 2)
      const blob = new Blob([data], { type: "application/json" })
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `validation_report_${documentId}.json`
      a.click()
      URL.revokeObjectURL(url)
      toast.success("Report exported")
    } catch (error) {
      console.error("Export error:", error)
      toast.error("Failed to export report")
    }
  }

  const handleDelete = async () => {
    try {
      await deleteDocument(documentId)
      toast.success("Document deleted")
      router.push("/")
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to delete document"
      console.error("Delete error:", error)
      toast.error(errorMessage)
    }
  }

  const isLoading = status?.status !== "completed" && status?.status !== "failed"

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/">
                <Button variant="ghost" size="icon">
                  <ArrowLeft className="h-5 w-5" />
                </Button>
              </Link>
              <div>
                <h1 className="font-semibold text-foreground">{results?.filename || "Loading..."}</h1>
                <p className="text-sm text-muted-foreground">Document ID: {documentId}</p>
                {results?.metadata && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {(results.metadata.societe_de_gestion || results.metadata["Société de Gestion"]) && (
                      <span className="text-xs bg-muted text-muted-foreground px-2 py-1 rounded">
                        <span className="font-medium">Société:</span> {results.metadata.societe_de_gestion || results.metadata["Société de Gestion"]}
                      </span>
                    )}
                    {(results.metadata.client_type || results.metadata["Le client est-il un professionnel"] !== undefined) && (
                      <span className="text-xs bg-muted text-muted-foreground px-2 py-1 rounded">
                        <span className="font-medium">Client:</span> {results.metadata.client_type === "professional" || results.metadata["Le client est-il un professionnel"] ? "Professional" : "Non-Professional"}
                      </span>
                    )}
                    {(results.metadata.new_strategy || results.metadata["Le document fait-il référence à une nouvelle Stratégie"]) && (
                      <span className="text-xs bg-blue-500/10 text-blue-600 px-2 py-1 rounded">
                        New Strategy
                      </span>
                    )}
                    {(results.metadata.new_product || results.metadata["Le document fait-il référence à un nouveau Produit"]) && (
                      <span className="text-xs bg-blue-500/10 text-blue-600 px-2 py-1 rounded">
                        New Product
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2">
              {!isLoading && results && <StatusBadge status={results.overall_status} />}
              <Button variant="ghost" size="icon" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
                <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
                <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
              </Button>
            </div>
          </div>

          {isLoading && (
            <div className="mt-4">
              <ProgressSteps currentStatus={status?.status || "pending"} />
            </div>
          )}
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Metrics Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="pt-6 flex items-center justify-center">
              <ComplianceScoreGauge score={results?.compliance_score || 0} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Issues</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-foreground">{results?.total_issues || 0}</div>
              <div className="flex items-center gap-2 mt-2 text-sm">
                <span className="text-critical">
                  {(results?.issues_by_severity.error || 0) + (results?.issues_by_severity.critical || 0)} critical
                </span>
                <span className="text-muted-foreground">·</span>
                <span className="text-high">
                  {(results?.issues_by_severity.warning || 0) + (results?.issues_by_severity.high || 0)} high
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Status</CardTitle>
            </CardHeader>
            <CardContent>
              {results && <StatusBadge status={results.overall_status} />}
              <p className="text-sm text-muted-foreground mt-2">
                {results?.compliance_score && results.compliance_score >= 80
                  ? "Document meets compliance standards"
                  : "Review required before approval"}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              <Button size="sm" variant="outline" onClick={handleExportJSON}>
                <FileJson className="h-4 w-4 mr-1" />
                Export
              </Button>
              <Button size="sm" variant="outline" onClick={handleDownload} disabled={isDownloading}>
                {isDownloading ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
                    Generating PDF...
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4 mr-1" />
                    Download
                  </>
                )}
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="text-destructive hover:text-destructive bg-transparent"
                onClick={handleDelete}
              >
                <Trash2 className="h-4 w-4 mr-1" />
                Delete
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <div className="grid lg:grid-cols-4 gap-6">
          {/* Sidebar Filters */}
          <div className="space-y-4">
            <CategoryFilter
              categories={categoryCounts}
              selected={selectedCategories.map((c) => categoryLabels[c] || c)}
              onToggle={(label) => {
                const key = Object.entries(categoryLabels).find(([, v]) => v === label)?.[0]
                if (key) toggleCategory(key)
              }}
            />
            <SeverityFilter selected={selectedSeverities} onToggle={toggleSeverity} />
            <Button variant="outline" className="w-full bg-transparent" onClick={resetFilters}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Reset Filters
            </Button>
          </div>

          {/* Issues List */}
          <div className="lg:col-span-3 space-y-4">
            {/* Search and Sort */}
            <div className="flex items-center gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search issues..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
              <Select value={sortOption} onValueChange={(v) => setSortOption(v as SortOption)}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="severity">Severity</SelectItem>
                  <SelectItem value="location">Location</SelectItem>
                  <SelectItem value="category">Category</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Issues */}
            {filteredIssues.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <PartyPopper className="h-12 w-12 mx-auto mb-4 text-success" />
                  <h3 className="text-lg font-medium text-foreground mb-2">No issues found!</h3>
                  <p className="text-muted-foreground">
                    {allIssues.length === 0
                      ? "Your document is fully compliant."
                      : "No issues match your current filters."}
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {filteredIssues.map((issue: Issue, index: number) => (
                  <IssueCard
                    key={`${issue.issue_type}-${issue.location}-${index}`}
                    issue={issue}
                    onApplyFix={issue.auto_fixable ? () => handleApplyFix(issue) : undefined}
                    onMarkReviewed={() => handleMarkReviewed(issue)}
                    onIgnore={() => handleIgnore(issue)}
                  />
                ))}
              </div>
            )}

            {/* Statistics */}
            {results?.statistics && <StatisticsTable statistics={results.statistics} />}
          </div>
        </div>
      </main>
    </div>
  )
}
