"use client"

import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { AlertCircle, AlertTriangle, Info, MinusCircle } from "lucide-react"
import type { SeverityFilter as SeverityType } from "@/lib/types"

interface SeverityFilterProps {
  selected: SeverityType[]
  onToggle: (severity: SeverityType) => void
}

const severities: { value: SeverityType; label: string; icon: typeof AlertCircle; color: string }[] = [
  { value: "error", label: "Error", icon: AlertCircle, color: "text-critical" },
  { value: "warning", label: "Warning", icon: AlertTriangle, color: "text-high" },
  { value: "critical", label: "Critical", icon: AlertCircle, color: "text-critical" },
  { value: "high", label: "High", icon: AlertTriangle, color: "text-high" },
  { value: "medium", label: "Medium", icon: Info, color: "text-medium" },
  { value: "low", label: "Low", icon: MinusCircle, color: "text-low" },
]

export function SeverityFilter({ selected, onToggle }: SeverityFilterProps) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <p className="text-sm font-medium text-foreground mb-3">Severity</p>
      <div className="space-y-2">
        {severities.map((severity) => (
          <div key={severity.value} className="flex items-center gap-2">
            <Checkbox
              id={severity.value}
              checked={selected.includes(severity.value)}
              onCheckedChange={() => onToggle(severity.value)}
            />
            <Label htmlFor={severity.value} className="flex items-center gap-2 cursor-pointer text-sm text-foreground">
              <severity.icon className={`h-4 w-4 ${severity.color}`} />
              {severity.label}
            </Label>
          </div>
        ))}
      </div>
    </div>
  )
}
