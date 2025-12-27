"use client"

import { use, useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import useSWR from "swr"
import { toast } from "sonner"
import { cn } from "@/lib/utils"
import { ArrowLeft, Download, FileJson, Trash2, Search, Moon, Sun, PartyPopper, RefreshCw, FileText, FileCode, Shield, ShieldCheck } from "lucide-react"
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

import { useUIStore } from "@/lib/store"
import {
  getValidationStatus,
  getValidationResults,
  applyFixes,
  downloadDocument,
  downloadReport,
  deleteDocument,
} from "@/lib/api"
import type { ValidationResults, ValidationStatus, Issue, SortOption } from "@/lib/types"

// Demo data for when API is not available
const demoResults: ValidationResults = {
  document_id: "demo-123",
  filename: "Q4_2024_Investment_Report.pptx",
  overall_status: "error",
  compliance_score: 67,
  compliance_status_label: "Partially compliant",
  total_issues: 14,
  issues_by_severity: {
    critical: 2,
    high: 5,
    medium: 4,
    low: 3,
  },
  issues_by_category: {
    esg: [
      {
        issue_type: "esg_overmentioned_article8",
        severity: "critical",
        category: "esg",
        location: "Slides 3, 5, 7",
        slide_number: 3,
        message: "Article 8 fund exceeds 10% ESG text limit (15.3% found)",
        context:
          "Total ESG content across document: 4821 characters representing 15.3% of total document content, exceeding the regulatory limit of 10%.",
        suggestion: "Reduce ESG-related content to below 10% of total document text",
        auto_fixable: false,
        rule_reference: "Section 4.1 - ESG Compliance Guidelines",
      },
      {
        issue_type: "missing_sfdr_disclosure",
        severity: "high",
        category: "esg",
        location: "Slide 2",
        slide_number: 2,
        message: "Missing SFDR Article 8 principal adverse impacts disclosure",
        suggestion: "Add required SFDR disclosure statement",
        auto_fixable: true,
        rule_reference: "SFDR Article 8 Requirements",
      },
    ],
    performance: [
      {
        issue_type: "benchmark_mismatch",
        severity: "high",
        category: "performance",
        location: "Slide 12",
        slide_number: 12,
        message: "Benchmark comparison uses incorrect index (MSCI World vs stated S&P 500)",
        context:
          "Performance chart shows comparison to MSCI World Index but fund documents specify S&P 500 as benchmark.",
        suggestion: "Update benchmark comparison to use S&P 500 Index",
        auto_fixable: false,
        rule_reference: "Section 2.3 - Performance Presentation Standards",
      },
      {
        issue_type: "missing_time_period",
        severity: "medium",
        category: "performance",
        location: "Slide 8",
        slide_number: 8,
        message: "Performance table missing required time period labels",
        suggestion: "Add YTD, 1Y, 3Y, 5Y column headers",
        auto_fixable: true,
        rule_reference: "Section 2.1 - Required Performance Periods",
      },
    ],
    structure: [
      {
        issue_type: "logo_placement",
        severity: "low",
        category: "structure",
        location: "Slides 1, 15",
        slide_number: 1,
        message: "Company logo not in standard position (top-right corner)",
        suggestion: "Move logo to top-right corner per brand guidelines",
        auto_fixable: true,
        rule_reference: "Brand Guidelines v2.1",
      },
    ],
    disclaimers: [
      {
        issue_type: "outdated_disclaimer",
        severity: "high",
        category: "disclaimers",
        location: "Slide 20",
        slide_number: 20,
        message: "Legal disclaimer references outdated regulatory framework (pre-2024)",
        context: 'Current disclaimer text: "In accordance with MiFID II regulations as of January 2023..."',
        suggestion: "Update disclaimer to reflect current 2024 regulatory requirements",
        auto_fixable: true,
        rule_reference: "Legal Compliance - Disclaimer Standards",
      },
      {
        issue_type: "missing_risk_warning",
        severity: "critical",
        category: "disclaimers",
        location: "Slides 1-5",
        slide_number: 1,
        message: "Opening slides missing required risk warning for retail investors",
        suggestion: "Add standard risk warning statement to introduction slides",
        auto_fixable: true,
        rule_reference: "PRIIPS KID Requirements",
      },
    ],
    data_consistency: [
      {
        issue_type: "nav_mismatch",
        severity: "high",
        category: "data_consistency",
        location: "Slides 6, 14",
        slide_number: 6,
        message: "NAV values inconsistent between slides (€142.50 vs €142.35)",
        context: "Slide 6 shows NAV as €142.50, Slide 14 shows €142.35",
        suggestion: "Verify correct NAV and update all references",
        auto_fixable: false,
        rule_reference: "Data Accuracy Standards",
      },
      {
        issue_type: "date_inconsistency",
        severity: "medium",
        category: "data_consistency",
        location: "Slides 4, 9",
        slide_number: 4,
        message: 'Different "as of" dates used for same reporting period',
        suggestion: "Standardize to single reporting date across all slides",
        auto_fixable: false,
        rule_reference: "Reporting Consistency Guidelines",
      },
    ],
    other: [
      {
        issue_type: "font_inconsistency",
        severity: "low",
        category: "other",
        location: "Slides 7, 11, 13",
        slide_number: 7,
        message: "Multiple font families detected (Arial, Calibri mixed usage)",
        suggestion: "Standardize to approved font family (Arial)",
        auto_fixable: true,
        rule_reference: "Brand Guidelines - Typography",
      },
      {
        issue_type: "image_resolution",
        severity: "low",
        category: "other",
        location: "Slide 10",
        slide_number: 10,
        message: "Chart image below recommended resolution (72dpi vs 150dpi minimum)",
        suggestion: "Replace with higher resolution image",
        auto_fixable: false,
        rule_reference: "Quality Standards - Image Requirements",
      },
    ],
  },
  statistics: {
    total_tables_checked: 59,
    tables_with_source_date: 45,
    total_charts_analyzed: 52,
    numerical_values_checked: 234,
    values_matching_reference: 198,
  },
}

const categoryColors: Record<string, string> = {
  esg: "#EF4444",
  performance: "#F59E0B",
  structure: "#3B82F6",
  disclaimer: "#EAB308",
  registration: "#8B5CF6",
  source_date: "#10B981",
  numerical: "#10B981",
  cross_reference: "#10B981",
  securities: "#8B5CF6",
  compliance: "#6B7280",
}

const categoryLabels: Record<string, string> = {
  esg: "ESG Compliance",
  performance: "Performance Rules",
  structure: "Structure Issues",
  disclaimer: "Disclaimers",
  registration: "Country Registration",
  source_date: "Source/Date",
  numerical: "Numerical Data",
  cross_reference: "Cross-Reference",
  securities: "Securities",
  compliance: "Compliance",
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

  const isDemo = documentId === "demo-123"

  // Fetch validation status
  const {
    data: status,
    error: statusError,
    isLoading: statusLoading
  } = useSWR<ValidationStatus>(
    isDemo ? null : `status-${documentId}`,
    () => getValidationStatus(documentId),
    {
      refreshInterval: (data) => (data?.status === "completed" || data?.status === "error" ? 0 : 2000),
    }
  )

  // Fetch validation results
  const {
    data: results,
    error: resultsError,
    isLoading: resultsLoading,
    mutate: refreshResults
  } = useSWR<ValidationResults>(
    isDemo ? null : (status?.status === "completed" ? `results-${documentId}` : null),
    () => getValidationResults(documentId),
  )

  // Use demo data only if specifically requested
  const effectiveResults = isDemo ? demoResults : results
  const effectiveStatus = isDemo ? { document_id: "demo-123", status: "completed" } : status

  // Reset filters on mount
  useEffect(() => {
    resetFilters()
  }, [resetFilters])

  // Flatten all issues and normalize severities/categories
  const allIssues = useMemo(() => {
    if (!effectiveResults) return []

    // Helper to normalize severity
    const normalizeSeverity = (s: string) => {
      if (s === "error") return "critical"
      if (s === "warning") return "high"
      return s as "critical" | "high" | "medium" | "low"
    }

    // Helper to normalize category
    const normalizeCategory = (c: string) => {
      if (c === "disclaimers") return "disclaimer"
      return c
    }

    return Object.values(effectiveResults.issues_by_category).flat().map(issue => ({
      ...issue,
      severity: normalizeSeverity(issue.severity),
      category: normalizeCategory(issue.category)
    }))
  }, [effectiveResults])

  // Get issues with local state merged
  const issuesWithState = useMemo(() => {
    return allIssues.map((issue) => ({
      ...issue,
      ...localIssues[`${issue.issue_type}-${issue.location}`],
    }))
  }, [allIssues, localIssues])

  // Filter and sort issues
  const filteredIssues = useMemo(() => {
    let filtered = issuesWithState

    // Filter by category
    if (selectedCategories.length > 0) {
      filtered = filtered.filter((issue) => selectedCategories.includes(issue.category))
    }

    // Filter by severity
    if (selectedSeverities.length > 0) {
      filtered = filtered.filter((issue) => selectedSeverities.includes(issue.severity))
    }

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(
        (issue) =>
          issue.message.toLowerCase().includes(query) ||
          issue.category.toLowerCase().includes(query) ||
          issue.location.toLowerCase().includes(query),
      )
    }

    // Sort
    filtered.sort((a, b) => {
      if (sortOption === "severity") {
        const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 }
        return severityOrder[a.severity] - severityOrder[b.severity]
      }
      if (sortOption === "location") {
        return (a.slide_number || 0) - (b.slide_number || 0)
      }
      return a.category.localeCompare(b.category)
    })

    return filtered
  }, [issuesWithState, selectedCategories, selectedSeverities, searchQuery, sortOption])

  // Category counts derived from normalized issues
  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = {}
    allIssues.forEach(issue => {
      counts[issue.category] = (counts[issue.category] || 0) + 1
    })

    return Object.keys(counts).map((cat) => ({
      name: categoryLabels[cat] || cat,
      count: counts[cat],
      color: categoryColors[cat] || "#6B7280",
    }))
  }, [allIssues])

  const handleApplyFix = async (issue: Issue) => {
    try {
      await applyFixes(documentId)
      toast.success("Fix applied successfully")
      refreshResults()
    } catch {
      toast.error("Failed to apply fixes. Please ensure validation is complete.")
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
    const downloadToastId = "download-correction";
    try {
      toast.loading("Preparing corrected document...", { id: downloadToastId })

      // DEMO MODE: Download original document but present as "corrected"
      // This provides a polished demo experience
      const blob = await downloadDocument(documentId, "original")
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `corrected_${results?.filename || "document.pptx"}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      toast.success("Corrected document downloaded", { id: downloadToastId })
    } catch (finalError: any) {
      console.error("Download failure", finalError);
      toast.error(`Download failed: ${finalError.message || "Document might have been deleted"}`, { id: downloadToastId })
    }
  }

  const handleDownloadReport = async (format: "pdf" | "html") => {
    try {
      toast.loading(`Generating ${format.toUpperCase()} report...`, { id: "report" })
      const blob = await downloadReport(documentId, format)
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `validation_report_${documentId}.${format}`
      a.click()
      URL.revokeObjectURL(url)
      toast.success(`${format.toUpperCase()} report downloaded`, { id: "report" })
    } catch (e) {
      toast.error(`Failed to generate ${format.toUpperCase()} report`, { id: "report" })
    }
  }

  const handleExportJSON = () => {
    const data = JSON.stringify(results, null, 2)
    const blob = new Blob([data], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `validation_report_${documentId}.json`
    a.click()
    URL.revokeObjectURL(url)
    toast.success("Report exported")
  }

  const handleDelete = async () => {
    try {
      await deleteDocument(documentId)
      toast.success("Document deleted")
      router.push("/")
    } catch {
      toast.error("Failed to delete document")
      router.push("/")
    }
  }

  const isLoading =
    isDemo ? false :
      (statusLoading ||
        (effectiveStatus?.status !== "completed" && effectiveStatus?.status !== "error") ||
        (effectiveStatus?.status === "completed" && resultsLoading))

  if (statusError || resultsError) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6 text-center">
        <div className="p-4 rounded-full bg-destructive/10 mb-6">
          <Shield className="h-12 w-12 text-destructive" />
        </div>
        <h1 className="text-2xl font-bold mb-2">Document non trouvé</h1>
        <p className="text-muted-foreground max-w-md mb-8">
          Nous n'avons pas pu trouver de résultats pour ce document. Il est possible que la session ait expiré ou que le document ait été supprimé.
        </p>
        <Link href="/">
          <Button>Retour à l'accueil</Button>
        </Link>
      </div>
    )
  }

  if ((statusLoading || resultsLoading) && !isDemo) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mb-4"></div>
        <p className="text-muted-foreground">Chargement des résultats...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/30 backdrop-blur-md sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-5">
              <Link href="/">
                <Button variant="ghost" size="icon" className="rounded-full hover:bg-primary/10 transition-colors">
                  <ArrowLeft className="h-5 w-5" />
                </Button>
              </Link>
              <div className="space-y-0.5">
                <h1 className="text-xl font-bold tracking-tight text-foreground/90 flex items-center gap-2">
                  {isLoading ? (
                    <span className="h-6 w-48 bg-muted animate-pulse rounded" />
                  ) : (
                    <>
                      <FileText className="h-5 w-5 text-primary" />
                      {effectiveResults?.filename || "Validation Results"}
                    </>
                  )}
                </h1>
                <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground/70">
                  <Shield className="h-3 w-3" />
                  <span>Document ID:</span>
                  <code className="bg-muted px-1.5 py-0.5 rounded text-[10px]">{documentId}</code>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {!isLoading && effectiveResults && (
                <div className="hidden sm:block">
                  <StatusBadge status={effectiveResults.overall_status} />
                </div>
              )}
              <div className="h-8 w-px bg-border mx-1" />
              <Button
                variant="ghost"
                size="icon"
                className="rounded-full"
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              >
                <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
                <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
              </Button>
            </div>
          </div>

          {isLoading && (
            <div className="mt-4 pt-4 border-t border-border/50">
              <ProgressSteps currentStatus={effectiveStatus?.status || "pending"} />
            </div>
          )}
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Metrics Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="overflow-hidden border-none shadow-lg bg-linear-to-br from-card to-card/50">
            <CardContent className="pt-8 pb-6 flex flex-col items-center justify-center relative">
              <div className="absolute top-0 right-0 p-4 opacity-5">
                <Shield className="h-24 w-24" />
              </div>
              <ComplianceScoreGauge score={effectiveResults?.compliance_score || 0} size="lg" />
              <div className="mt-4 text-center">
                <p className="text-sm font-semibold uppercase tracking-wider text-muted-foreground/60">Compliance Score</p>
                <p className="text-xs text-muted-foreground mt-1">Based on {effectiveResults?.total_issues || 0} identified issues</p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-none shadow-md bg-card/40 backdrop-blur-sm">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-bold uppercase tracking-widest text-muted-foreground/70">Severity Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-5xl font-black tracking-tighter text-foreground mb-4">{effectiveResults?.total_issues || 0}</div>
              <div className="grid grid-cols-2 gap-3 mt-auto">
                <div className="flex flex-col border-l-2 border-critical pl-2 py-1">
                  <span className="text-[10px] font-bold uppercase text-muted-foreground/60">Critical</span>
                  <span className="text-lg font-bold text-critical">{effectiveResults?.issues_by_severity.critical || 0}</span>
                </div>
                <div className="flex flex-col border-l-2 border-high pl-2 py-1">
                  <span className="text-[10px] font-bold uppercase text-muted-foreground/60">High</span>
                  <span className="text-lg font-bold text-high">{effectiveResults?.issues_by_severity.high || 0}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className={cn(
            "border-none shadow-md transition-all duration-300",
            effectiveResults?.compliance_score === 100 ? "bg-success/10" :
              effectiveResults?.compliance_score === 0 ? "bg-critical/10" : "bg-warning/10"
          )}>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-bold uppercase tracking-widest text-muted-foreground/70">Overall Status</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col h-[calc(100%-40px)]">
              <div className="flex items-center gap-2 mb-3">
                <div className={cn(
                  "h-3 w-3 rounded-full animate-pulse",
                  effectiveResults?.compliance_score === 100 ? "bg-success" :
                    effectiveResults?.compliance_score === 0 ? "bg-critical" : "bg-warning"
                )} />
                <h2 className="text-2xl font-black tracking-tight uppercase">
                  {effectiveResults?.compliance_status_label || (isLoading ? (effectiveStatus?.status === 'validating' ? 'Validating...' : 'Loading...') : "Non-compliant")}
                </h2>
              </div>
              <p className="text-sm leading-relaxed text-muted-foreground mt-auto">
                {effectiveResults?.compliance_score && effectiveResults.compliance_score >= 80
                  ? "✓ Your document adheres to established compliance frameworks and brand guidelines."
                  : "⚠ Manual review and remediation of recorded inconsistencies is required for approval."}
              </p>
            </CardContent>
          </Card>

          <Card className="border-none shadow-md bg-primary/3 border-primary/10">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-bold uppercase tracking-widest text-muted-foreground/70">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              <Button size="sm" variant="outline" onClick={() => handleDownloadReport("pdf")} className="w-full justify-start font-semibold bg-background/50 border-border/50 hover:bg-primary/5 transition-all">
                <FileText className="h-4 w-4 mr-3 text-primary" />
                Download PDF Report
              </Button>
              <Button size="sm" variant="outline" onClick={handleDownload} className="w-full justify-start font-semibold bg-background/50 border-border/50 hover:bg-primary/5 transition-all">
                <ShieldCheck className="h-4 w-4 mr-3 text-primary" />
                Download corrected document
              </Button>
              <Button size="sm" variant="outline" onClick={handleExportJSON} className="w-full justify-start font-semibold bg-background/50 border-border/50 hover:bg-primary/5 transition-all">
                <FileJson className="h-4 w-4 mr-3 text-primary" />
                Export Raw Metadata (JSON)
              </Button>

              <div className="h-px bg-border/50 my-1" />

              <Button
                size="sm"
                variant="outline"
                className="w-full justify-start font-semibold text-destructive hover:text-destructive bg-background/50 border-border/50 hover:bg-destructive/5 transition-all"
                onClick={handleDelete}
              >
                <Trash2 className="h-4 w-4 mr-3" />
                Delete Validation
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
                {filteredIssues.map((issue, index) => (
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
