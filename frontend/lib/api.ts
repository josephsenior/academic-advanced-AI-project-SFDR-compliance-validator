import type { Document, ValidationResults, ValidationStatus, DocumentMetadata } from "./types"

const API_BASE = "http://localhost:5000/api/v1"

export async function uploadDocument(file: File, metadata?: DocumentMetadata): Promise<{ document_id: string }> {
  const formData = new FormData()
  formData.append("file", file)
  if (metadata) {
    formData.append("metadata", JSON.stringify(metadata))
  }

  const response = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  })

  if (!response.ok) {
    throw new Error("Upload failed")
  }
  return response.json()
}

export async function validateDocument(documentId: string, options?: Record<string, unknown>): Promise<void> {
  const response = await fetch(`${API_BASE}/validate/${documentId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(options || {}),
  })

  if (!response.ok) {
    throw new Error("Validation failed")
  }
}

export async function getValidationStatus(documentId: string): Promise<ValidationStatus> {
  const response = await fetch(`${API_BASE}/status/${documentId}`)

  if (!response.ok) {
    throw new Error("Failed to fetch status")
  }
  return response.json()
}

export async function getValidationResults(documentId: string): Promise<ValidationResults> {
  const response = await fetch(`${API_BASE}/results/${documentId}`)

  if (!response.ok) {
    throw new Error("Failed to fetch results")
  }
  return response.json()
}

export async function applyFixes(documentId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/fix/${documentId}`, {
    method: "POST",
  })

  if (!response.ok) {
    throw new Error("Failed to apply fixes")
  }
}

export async function downloadCorrectedDocument(documentId: string): Promise<Blob> {
  const response = await fetch(`${API_BASE}/download/${documentId}?type=corrected`)

  if (!response.ok) {
    throw new Error("Failed to download document")
  }
  return response.blob()
}

export async function listDocuments(): Promise<Document[]> {
  const response = await fetch(`${API_BASE}/list`)

  if (!response.ok) {
    throw new Error("Failed to list documents")
  }
  return response.json()
}

export async function deleteDocument(documentId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/delete/${documentId}`, {
    method: "DELETE",
  })

  if (!response.ok) {
    throw new Error("Failed to delete document")
  }
}
