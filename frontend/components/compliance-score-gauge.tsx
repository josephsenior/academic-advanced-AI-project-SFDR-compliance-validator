"use client"

import { useEffect, useState } from "react"
import { cn } from "@/lib/utils"

interface ComplianceScoreGaugeProps {
  score: number
  size?: "sm" | "md" | "lg"
}

export function ComplianceScoreGauge({ score, size = "md" }: ComplianceScoreGaugeProps) {
  const [displayScore, setDisplayScore] = useState(0)

  useEffect(() => {
    const duration = 1000
    const start = Date.now()
    const startScore = displayScore

    const animate = () => {
      const elapsed = Date.now() - start
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplayScore(Math.round(startScore + (score - startScore) * eased))

      if (progress < 1) {
        requestAnimationFrame(animate)
      }
    }

    requestAnimationFrame(animate)
  }, [score])

  const sizes = {
    sm: { container: "w-24 h-24", text: "text-2xl", label: "text-xs" },
    md: { container: "w-32 h-32", text: "text-3xl", label: "text-sm" },
    lg: { container: "w-40 h-40", text: "text-4xl", label: "text-base" },
  }

  const circumference = 2 * Math.PI * 45
  const strokeDashoffset = circumference - (displayScore / 100) * circumference

  const getScoreColor = () => {
    if (displayScore >= 80) return "text-success stroke-success"
    if (displayScore >= 60) return "text-medium stroke-medium"
    if (displayScore >= 40) return "text-high stroke-high"
    return "text-critical stroke-critical"
  }

  return (
    <div className={cn("relative", sizes[size].container)}>
      <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="8" className="text-muted/30" />
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className={cn("transition-all duration-1000", getScoreColor())}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={cn("font-bold", sizes[size].text, getScoreColor())}>{displayScore}</span>
        <span className={cn("text-muted-foreground", sizes[size].label)}>Score</span>
      </div>
    </div>
  )
}
