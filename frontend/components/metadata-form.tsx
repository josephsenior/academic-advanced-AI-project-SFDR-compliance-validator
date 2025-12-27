"use client"

import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Checkbox } from "@/components/ui/checkbox"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import type { DocumentMetadata } from "@/lib/types"

interface MetadataFormProps {
  metadata: DocumentMetadata
  onChange: (metadata: DocumentMetadata) => void
}

export function MetadataForm({ metadata, onChange }: MetadataFormProps) {
  return (
    <div className="space-y-6 p-6 rounded-xl bg-card border border-border">
      <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide">Métadonnées du Document</h3>

      <div className="space-y-4">
        {/* Société de Gestion */}
        <div className="space-y-2">
          <Label className="text-foreground font-medium">Société de Gestion</Label>
          <Select
            value={metadata.societe_de_gestion || "ODDO BHF ASSET MANAGEMENT SAS"}
            onValueChange={(v) => onChange({ ...metadata, societe_de_gestion: v })}
          >
            <SelectTrigger className="bg-background">
              <SelectValue placeholder="Sélectionner une société" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ODDO BHF ASSET MANAGEMENT SAS">ODDO BHF ASSET MANAGEMENT SAS</SelectItem>
              <SelectItem value="ODDO BHF ASSET MANAGEMENT GmbH">ODDO BHF ASSET MANAGEMENT GmbH</SelectItem>
              <SelectItem value="ODDO BHF ASSET MANAGEMENT Lux">ODDO BHF ASSET MANAGEMENT Lux</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* SICAV Toggle */}
        <div className="flex items-center justify-between py-2 border-b border-border/50">
          <Label className="text-foreground">
            Est ce que le produit fait partie de la Sicav ?
          </Label>
          <Switch
            checked={metadata.is_sicav || false}
            onCheckedChange={(checked) => onChange({ ...metadata, is_sicav: checked })}
          />
        </div>

        {/* Professional Client Toggle */}
        <div className="flex items-center justify-between py-2 border-b border-border/50">
          <Label className="text-foreground">
            Le client est-il un professionnel ?
          </Label>
          <Switch
            checked={metadata.is_professional_client || false}
            onCheckedChange={(checked) => onChange({ ...metadata, is_professional_client: checked })}
          />
        </div>

        {/* New Strategy Checkbox */}
        <div className="flex items-center gap-3 pt-2">
          <Checkbox
            id="new-strategy"
            checked={metadata.is_new_strategy || false}
            onCheckedChange={(checked) => onChange({ ...metadata, is_new_strategy: checked as boolean })}
          />
          <Label htmlFor="new-strategy" className="text-sm text-foreground cursor-pointer">
            Le document fait-il référence à une nouvelle Stratégie ?
          </Label>
        </div>

        {/* New Product Checkbox */}
        <div className="flex items-center gap-3">
          <Checkbox
            id="new-product"
            checked={metadata.is_new_product || false}
            onCheckedChange={(checked) => onChange({ ...metadata, is_new_product: checked as boolean })}
          />
          <Label htmlFor="new-product" className="text-sm text-foreground cursor-pointer">
            Le document fait-il référence à un nouveau Produit ?
          </Label>
        </div>
      </div>
    </div>
  )
}
