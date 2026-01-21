import type { Document, ValidationResults, ValidationStatus, DocumentMetadata } from "./types"

const API_BASE = "http://localhost:5000/api/v1"

type UploadParams = {
  document: File
  metadata?: DocumentMetadata
  metadataFile?: File
  prospectusFile?: File
}

export async function uploadDocument(params: UploadParams): Promise<{ document_id: string }>
export async function uploadDocument(document: File, metadata?: DocumentMetadata): Promise<{ document_id: string }>
export async function uploadDocument(
  arg1: UploadParams | File,
  arg2?: DocumentMetadata,
): Promise<{ document_id: string }> {
  const formData = new FormData()

  if (arg1 instanceof File) {
    formData.append("document", arg1)
    if (arg2) {
      formData.append("metadata", JSON.stringify(arg2))
    }
  } else {
    formData.append("document", arg1.document)
    if (arg1.metadataFile) {
      formData.append("metadata", arg1.metadataFile)
    } else if (arg1.metadata) {
      formData.append("metadata", JSON.stringify(arg1.metadata))
    }
    if (arg1.prospectusFile) {
      formData.append("prospectus", arg1.prospectusFile)
    }
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
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({}),
  })

  if (!response.ok) {
    let errorMessage = "Failed to apply fixes";
    try {
      const errorData = await response.json();
      errorMessage = errorData.error || errorMessage;
    } catch (e) {
      // Not JSON
    }
    throw new Error(errorMessage)
  }
}

export async function downloadDocument(documentId: string, type: "original" | "corrected" = "corrected"): Promise<Blob> {
  const response = await fetch(`${API_BASE}/download/${documentId}?type=${type}`)

  if (!response.ok) {
    let errorMessage = `Failed to download ${type} document`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.error || errorMessage;
    } catch (e) {
      // If not JSON, use default or status text
      if (response.status === 404) {
        errorMessage = `${type} document not found`;
      }
    }
    throw new Error(errorMessage);
  }
  return response.blob()
}


export async function downloadReport(documentId: string, format: "pdf" | "html"): Promise<Blob> {
  const response = await fetch(`${API_BASE}/report/${documentId}?format=${format}`)

  if (!response.ok) {
    throw new Error(`Failed to download ${format} report`)
  }
  return response.blob()
}

export async function listDocuments(): Promise<Document[]> {
  const response = await fetch(`${API_BASE}/list`)

  if (!response.ok) {
    throw new Error("Failed to list documents")
  }
  const data = await response.json()
  // Backend returns an object { total, limit, offset, documents }
  // Ensure we return an array of documents for the frontend components
  if (data && Array.isArray(data.documents)) {
    return data.documents
  }
  // Fallback: if backend returned an array directly, return it
  if (Array.isArray(data)) {
    return data
  }
  return []
}

export async function deleteDocument(documentId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/delete/${documentId}`, {
    method: "DELETE",
  })

  if (!response.ok) {
    throw new Error("Failed to delete document")
  }
}
