import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { Statistics } from "@/lib/types"
import { Table, BarChart3, Hash, CheckCheck } from "lucide-react"

interface StatisticsTableProps {
  statistics: Statistics
}

export function StatisticsTable({ statistics }: StatisticsTableProps) {
  const stats = [
    {
      label: "Tables Checked",
      value: statistics.total_tables_checked,
      icon: Table,
    },
    {
      label: "Tables with Source/Date",
      value: statistics.tables_with_source_date,
      icon: CheckCheck,
    },
    {
      label: "Charts Analyzed",
      value: statistics.total_charts_analyzed,
      icon: BarChart3,
    },
    {
      label: "Numerical Values Checked",
      value: statistics.numerical_values_checked || 0,
      icon: Hash,
    },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Validation Statistics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {stats.map((stat) => (
            <div key={stat.label} className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
              <stat.icon className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-2xl font-bold text-foreground">{stat.value}</p>
                <p className="text-xs text-muted-foreground">{stat.label}</p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
