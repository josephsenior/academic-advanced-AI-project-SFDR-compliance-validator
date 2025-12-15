import { cn } from "@/lib/utils"
import { AlertCircle, AlertTriangle, Info, MinusCircle } from "lucide-react"

interface SeverityBadgeProps {
  severity: "critical" | "high" | "medium" | "low"
  showIcon?: boolean
  className?: string
}

const severityConfig = {
  critical: {
    label: "Critical",
    className: "bg-critical/15 text-critical border-critical/30",
    icon: AlertCircle,
  },
  high: {
    label: "High",
    className: "bg-high/15 text-high border-high/30",
    icon: AlertTriangle,
  },
  medium: {
    label: "Medium",
    className: "bg-medium/15 text-medium border-medium/30",
    icon: Info,
  },
  low: {
    label: "Low",
    className: "bg-low/15 text-low border-low/30",
    icon: MinusCircle,
  },
}

export function SeverityBadge({ severity, showIcon = true, className }: SeverityBadgeProps) {
  const config = severityConfig[severity]
  const Icon = config.icon

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border",
        config.className,
        className,
      )}
    >
      {showIcon && <Icon className="h-3 w-3" />}
      {config.label}
    </span>
  )
}
