"use client"

import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Checkbox } from "@/components/ui/checkbox"
import type { DocumentMetadata } from "@/lib/types"

interface MetadataFormProps {
  metadata: DocumentMetadata
  onChange: (metadata: DocumentMetadata) => void
}

export function MetadataForm({ metadata, onChange }: MetadataFormProps) {
  return (
    <div className="space-y-6 p-6 rounded-xl bg-card border border-border">
      <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide">Document Metadata</h3>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="societe" className="text-foreground">
            Société de Gestion
          </Label>
          <Input
            id="societe"
            placeholder="Enter company name"
            value={metadata.societe_de_gestion || ""}
            onChange={(e) => onChange({ ...metadata, societe_de_gestion: e.target.value })}
            className="bg-background"
          />
        </div>

        <div className="flex items-center justify-between">
          <Label htmlFor="client-type" className="text-foreground">
            Client Type
          </Label>
          <div className="flex items-center gap-3">
            <span
              className={`text-sm ${metadata.client_type === "non-professional" ? "text-foreground" : "text-muted-foreground"}`}
            >
              Non-Professional
            </span>
            <Switch
              id="client-type"
              checked={metadata.client_type === "professional"}
              onCheckedChange={(checked) =>
                onChange({
                  ...metadata,
                  client_type: checked ? "professional" : "non-professional",
                })
              }
            />
            <span
              className={`text-sm ${metadata.client_type === "professional" ? "text-foreground" : "text-muted-foreground"}`}
            >
              Professional
            </span>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Checkbox
              id="new-strategy"
              checked={metadata.new_strategy || false}
              onCheckedChange={(checked) => onChange({ ...metadata, new_strategy: checked as boolean })}
            />
            <Label htmlFor="new-strategy" className="text-sm text-foreground">
              New Strategy
            </Label>
          </div>

          <div className="flex items-center gap-2">
            <Checkbox
              id="new-product"
              checked={metadata.new_product || false}
              onCheckedChange={(checked) => onChange({ ...metadata, new_product: checked as boolean })}
            />
            <Label htmlFor="new-product" className="text-sm text-foreground">
              New Product
            </Label>
          </div>
        </div>
      </div>
    </div>
  )
}
