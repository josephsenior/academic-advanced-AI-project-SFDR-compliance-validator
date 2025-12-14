"use client"

import { useState } from "react"
import { ChevronDown, Wrench, CheckCircle, EyeOff } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { SeverityBadge } from "@/components/severity-badge"
import type { Issue } from "@/lib/types"

interface IssueCardProps {
  issue: Issue
  onApplyFix?: () => void
  onMarkReviewed?: () => void
  onIgnore?: () => void
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

export function IssueCard({ issue, onApplyFix, onMarkReviewed, onIgnore }: IssueCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div
      className={cn(
        "rounded-lg border border-border bg-card overflow-hidden transition-all duration-200",
        issue.reviewed && "opacity-60",
        issue.ignored && "opacity-40",
      )}
    >
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 text-left hover:bg-accent/50 transition-colors"
      >
        <div className="flex items-start gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <SeverityBadge severity={issue.severity} />
              <span className="text-xs text-muted-foreground">{categoryLabels[issue.category] || issue.category}</span>
              {issue.slide_number && (
                <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded">Slide {issue.slide_number}</span>
              )}
              <span className="text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded font-mono">{issue.issue_type}</span>
            </div>
            <p className="font-medium text-foreground">{issue.message}</p>
            <p className="text-sm text-muted-foreground mt-1">{issue.location}</p>
          </div>
          <ChevronDown
            className={cn("h-5 w-5 text-muted-foreground transition-transform shrink-0", isExpanded && "rotate-180")}
          />
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 space-y-4 border-t border-border pt-4">
          {issue.context && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Context</p>
              <p className="text-sm text-foreground bg-muted/50 p-3 rounded-lg">{issue.context}</p>
            </div>
          )}

          {issue.suggestion && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Suggestion</p>
              <p className="text-sm text-foreground">{issue.suggestion}</p>
            </div>
          )}

          {issue.rule_reference && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Rule Reference</p>
              <p className="text-sm text-primary">{issue.rule_reference}</p>
            </div>
          )}

          <div className="flex items-center gap-2 pt-2">
            {issue.auto_fixable && onApplyFix && (
              <Button size="sm" onClick={onApplyFix} className="gap-1.5">
                <Wrench className="h-3.5 w-3.5" />
                Apply Fix
              </Button>
            )}
            {onMarkReviewed && !issue.reviewed && (
              <Button size="sm" variant="outline" onClick={onMarkReviewed} className="gap-1.5 bg-transparent">
                <CheckCircle className="h-3.5 w-3.5" />
                Mark as Reviewed
              </Button>
            )}
            {onIgnore && !issue.ignored && (
              <Button size="sm" variant="ghost" onClick={onIgnore} className="gap-1.5 text-muted-foreground">
                <EyeOff className="h-3.5 w-3.5" />
                Ignore
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
