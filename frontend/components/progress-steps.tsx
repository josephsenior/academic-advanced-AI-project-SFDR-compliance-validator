import { cn } from "@/lib/utils"
import { Check, Loader2 } from "lucide-react"

interface ProgressStepsProps {
  currentStatus: string
}

const steps = [
  { id: "uploading", label: "Uploading" },
  { id: "extracting", label: "Extracting" },
  { id: "validating", label: "Validating" },
  { id: "complete", label: "Complete" },
]

export function ProgressSteps({ currentStatus }: ProgressStepsProps) {
  const currentIndex = steps.findIndex((s) => s.id === currentStatus)

  return (
    <div className="flex items-center gap-2">
      {steps.map((step, index) => {
        const isComplete = index < currentIndex || currentStatus === "complete"
        const isCurrent = index === currentIndex && currentStatus !== "complete"

        return (
          <div key={step.id} className="flex items-center gap-2">
            <div
              className={cn(
                "flex items-center justify-center w-8 h-8 rounded-full border-2 transition-colors",
                isComplete && "bg-primary border-primary text-primary-foreground",
                isCurrent && "border-primary text-primary",
                !isComplete && !isCurrent && "border-muted text-muted-foreground",
              )}
            >
              {isComplete ? (
                <Check className="h-4 w-4" />
              ) : isCurrent ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <span className="text-xs">{index + 1}</span>
              )}
            </div>
            <span
              className={cn(
                "text-sm hidden sm:inline",
                isComplete || isCurrent ? "text-foreground" : "text-muted-foreground",
              )}
            >
              {step.label}
            </span>
            {index < steps.length - 1 && (
              <div className={cn("w-8 h-0.5 mx-2", index < currentIndex ? "bg-primary" : "bg-muted")} />
            )}
          </div>
        )
      })}
    </div>
  )
}
