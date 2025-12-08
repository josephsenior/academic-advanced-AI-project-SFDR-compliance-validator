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

import { useUIStore } from "@/lib/store"
import {
  getValidationStatus,
  getValidationResults,
  applyFixes,
  downloadCorrectedDocument,
  deleteDocument,
} from "@/lib/api"
import type { ValidationResults, ValidationStatus, Issue, SortOption } from "@/lib/types"

// Demo data for when API is not available
const demoResults: ValidationResults = {
  document_id: "demo-123",
  filename: "Q4_2024_Investment_Report.pptx",
  overall_status: "error",
  compliance_score: 67,
  total_issues: 14,
  issues_by_severity: {
    critical: 2,
    high: 5,
    medium: 4,
    low: 3,
  },
  category_counts: {
    esg: {
      total: 2,
      critical: 1,
      high: 1,
      medium: 0,
      low: 0,
    },
    performance: {
      total: 5,
      critical: 1,
      high: 2,
      medium: 1,
      low: 1,
    },
    disclaimers: {
      total: 4,
      critical: 0,
      high: 2,
      medium: 2,
      low: 0,
    },
    registration: {
      total: 3,
      critical: 0,
      high: 0,
      medium: 1,
      low: 2,
    },
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
    fallbackData: { 
      document_id: documentId, 
      filename: "", 
      status: "completed", 
      progress: 100,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    onError: () => {
      // Silent fail - use demo data
    },
  })

  // Fetch validation results
  const { data: results, mutate: refreshResults } = useSWR<ValidationResults>(
    status?.status === "completed" ? `results-${documentId}` : null,
    () => getValidationResults(documentId),
    {
      fallbackData: demoResults,
      onError: () => {
        // Silent fail - use demo data
      },
    },
  )

  // Reset filters on mount
  useEffect(() => {
    resetFilters()
  }, [resetFilters])

  // Flatten all issues
  const allIssues = useMemo(() => {
    if (!results) return []
    return Object.values(results.issues_by_category).flat()
  }, [results])

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
    } catch {
      toast.error("Failed to apply fix (demo mode)")
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
    try {
      const blob = await downloadCorrectedDocument(documentId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `corrected_${results?.filename || "document"}`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      toast.error("Download not available in demo mode")
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
      toast.error("Failed to delete (demo mode)")
      router.push("/")
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
                <span className="text-critical">{results?.issues_by_severity.critical || 0} critical</span>
                <span className="text-muted-foreground">·</span>
                <span className="text-high">{results?.issues_by_severity.high || 0} high</span>
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
              <Button size="sm" variant="outline" onClick={handleDownload}>
                <Download className="h-4 w-4 mr-1" />
                Download
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
