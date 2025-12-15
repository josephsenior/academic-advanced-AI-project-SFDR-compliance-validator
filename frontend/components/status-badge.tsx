import { cn } from "@/lib/utils"
import { CheckCircle, XCircle, AlertTriangle } from "lucide-react"

interface StatusBadgeProps {
  status: "pass" | "warning" | "error"
  className?: string
}

const statusConfig = {
  pass: {
    label: "Pass",
    className: "bg-success/15 text-success border-success/30",
    icon: CheckCircle,
  },
  warning: {
    label: "Warning",
    className: "bg-medium/15 text-medium border-medium/30",
    icon: AlertTriangle,
  },
  error: {
    label: "Error",
    className: "bg-critical/15 text-critical border-critical/30",
    icon: XCircle,
  },
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status]
  const Icon = config.icon

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium border",
        config.className,
        className,
      )}
    >
      <Icon className="h-4 w-4" />
      {config.label}
    </span>
  )
}
