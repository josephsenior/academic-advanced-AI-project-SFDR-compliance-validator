"use client"

import { cn } from "@/lib/utils"
import { ChevronDown } from "lucide-react"
import { useState } from "react"

interface CategoryFilterProps {
  categories: { name: string; count: number; color: string }[]
  selected: string[]
  onToggle: (category: string) => void
}

export function CategoryFilter({ categories, selected, onToggle }: CategoryFilterProps) {
  const [isExpanded, setIsExpanded] = useState(true)

  return (
    <div className="rounded-lg border border-border bg-card overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-accent/50 transition-colors"
      >
        <span className="text-sm font-medium text-foreground">Categories</span>
        <ChevronDown className={cn("h-4 w-4 text-muted-foreground transition-transform", isExpanded && "rotate-180")} />
      </button>

      {isExpanded && (
        <div className="px-2 pb-2 space-y-1">
          {categories.map((category) => (
            <button
              key={category.name}
              onClick={() => onToggle(category.name)}
              className={cn(
                "w-full flex items-center justify-between px-3 py-2 rounded-md text-sm transition-colors",
                selected.length === 0 || selected.includes(category.name)
                  ? "bg-accent text-foreground"
                  : "text-muted-foreground hover:bg-accent/50",
              )}
            >
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: category.color }} />
                {category.name}
              </span>
              <span
                className={cn(
                  "text-xs px-1.5 py-0.5 rounded",
                  category.count > 0 ? "bg-muted" : "text-muted-foreground",
                )}
              >
                {category.count}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
