export interface DocumentMetadata {
  societe_de_gestion?: string
  client_type?: "professional" | "non-professional"
  new_strategy?: boolean
  new_product?: boolean
}

export interface Document {
  document_id: string
  filename: string
  upload_date: string
  status: "pending" | "uploading" | "extracting" | "validating" | "complete" | "error"
  metadata?: DocumentMetadata
}

export interface Issue {
  issue_type: string
  severity: "critical" | "high" | "medium" | "low"
  category: string
  location: string
  slide_number?: number
  message: string
  context?: string
  suggestion?: string
  auto_fixable: boolean
  rule_reference?: string
  reviewed?: boolean
  ignored?: boolean
}

export interface IssuesByCategory {
  [category: string]: Issue[]
}

export interface IssuesBySeverity {
  critical: number
  high: number
  medium: number
  low: number
}

export interface Statistics {
  total_tables_checked: number
  tables_with_source_date: number
  total_charts_analyzed: number
  numerical_values_checked?: number
  values_matching_reference?: number
}

export interface ValidationResults {
  document_id: string
  filename?: string
  overall_status: "pass" | "warning" | "error"
  compliance_score: number
  total_issues: number
  issues_by_severity: IssuesBySeverity
  issues_by_category: IssuesByCategory
  statistics: Statistics
}

export interface ValidationStatus {
  document_id: string
  status: "pending" | "uploading" | "extracting" | "validating" | "complete" | "error"
  progress?: number
  message?: string
}

export type SortOption = "severity" | "location" | "category"
export type SeverityFilter = "critical" | "high" | "medium" | "low"
