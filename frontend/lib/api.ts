import type { Document, ValidationResults, ValidationStatus, DocumentMetadata } from "./types"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000/api/v1"

// Retry configuration
const MAX_RETRIES = 3
const RETRY_DELAY = 1000

class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string
  ) {
    super(message)
    this.name = "ApiError"
  }
}

async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  retries = MAX_RETRIES
): Promise<Response> {
  try {
    const response = await fetch(url, options)
    
    if (!response.ok && retries > 0 && response.status >= 500) {
      // Retry on server errors
      await new Promise(resolve => setTimeout(resolve, RETRY_DELAY))
      return fetchWithRetry(url, options, retries - 1)
    }
    
    return response
  } catch (error) {
    if (retries > 0) {
      await new Promise(resolve => setTimeout(resolve, RETRY_DELAY))
      return fetchWithRetry(url, options, retries - 1)
    }
    throw error
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new ApiError(
      errorData.message || `Request failed with status ${response.status}`,
      response.status,
      errorData.code
    )
  }
  return response.json()
}

export async function uploadDocument(
  documentFile: File,
  metadataFile?: File,
  prospectusFile?: File
): Promise<{ document_id: string; has_metadata: boolean; has_prospectus: boolean }> {
  const formData = new FormData()
  
  formData.append("document", documentFile)
  
  if (metadataFile) {
    formData.append("metadata", metadataFile)
  }
  
  if (prospectusFile) {
    formData.append("prospectus", prospectusFile)
  }

  try {
    const response = await fetchWithRetry(`${API_BASE}/upload`, {
      method: "POST",
      body: formData,
    })
    return handleResponse(response)
  } catch (error) {
    if (error instanceof ApiError) {
      throw new Error(`Upload failed: ${error.message}`)
    }
    throw new Error("Upload failed: Unable to connect to server")
  }
}

export async function validateDocument(documentId: string, options?: Record<string, unknown>): Promise<void> {
  try {
    const response = await fetchWithRetry(`${API_BASE}/validate/${documentId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(options || {}),
    })
    await handleResponse(response)
  } catch (error) {
    if (error instanceof ApiError) {
      throw new Error(`Validation failed: ${error.message}`)
    }
    throw new Error("Validation failed: Unable to connect to server")
  }
}

export async function getValidationStatus(documentId: string): Promise<ValidationStatus> {
  try {
    const response = await fetchWithRetry(`${API_BASE}/status/${documentId}`)
    return handleResponse(response)
  } catch (error) {
    if (error instanceof ApiError) {
      throw new Error(`Failed to fetch status: ${error.message}`)
    }
    throw new Error("Failed to fetch status: Unable to connect to server")
  }
}

export async function getValidationResults(documentId: string): Promise<ValidationResults> {
  try {
    const response = await fetchWithRetry(`${API_BASE}/results/${documentId}`)
    return handleResponse(response)
  } catch (error) {
    if (error instanceof ApiError) {
      throw new Error(`Failed to fetch results: ${error.message}`)
    }
    throw new Error("Failed to fetch results: Unable to connect to server")
  }
}

export async function applyFixes(documentId: string): Promise<void> {
  try {
    const response = await fetchWithRetry(`${API_BASE}/fix/${documentId}`, {
      method: "POST",
    })
    await handleResponse(response)
  } catch (error) {
    if (error instanceof ApiError) {
      throw new Error(`Failed to apply fixes: ${error.message}`)
    }
    throw new Error("Failed to apply fixes: Unable to connect to server")
  }
}

export async function downloadCorrectedDocument(documentId: string): Promise<Blob> {
  try {
    const response = await fetchWithRetry(`${API_BASE}/download/${documentId}?type=corrected`)
    if (!response.ok) {
      throw new ApiError(
        `Download failed with status ${response.status}`,
        response.status
      )
    }
    return response.blob()
  } catch (error) {
    if (error instanceof ApiError) {
      throw new Error(`Failed to download document: ${error.message}`)
    }
    throw new Error("Failed to download document: Unable to connect to server")
  }
}

export async function downloadReport(documentId: string, format: 'json' | 'html' | 'pdf' = 'html'): Promise<Blob> {
  try {
    const response = await fetchWithRetry(`${API_BASE}/report/${documentId}?format=${format}`)
    if (!response.ok) {
      const errText = await response.text().catch(() => '')
      throw new ApiError(`Report download failed with status ${response.status} ${errText}`, response.status)
    }
    return response.blob()
  } catch (error) {
    if (error instanceof ApiError) {
      throw new Error(`Failed to download report: ${error.message}`)
    }
    throw new Error('Failed to download report: Unable to connect to server')
  }
}

export async function listDocuments(): Promise<Document[]> {
  try {
    const response = await fetchWithRetry(`${API_BASE}/list`)
    const data = await handleResponse<{ documents?: Document[] }>(response)
    return data.documents || []
  } catch (error) {
    if (error instanceof ApiError) {
      throw new Error(`Failed to list documents: ${error.message}`)
    }
    throw new Error("Failed to list documents: Unable to connect to server")
  }
}

export async function deleteDocument(documentId: string): Promise<void> {
  try {
    const response = await fetchWithRetry(`${API_BASE}/delete/${documentId}`, {
      method: "DELETE",
    })
    await handleResponse(response)
  } catch (error) {
    if (error instanceof ApiError) {
      throw new Error(`Failed to delete document: ${error.message}`)
    }
    throw new Error("Failed to delete document: Unable to connect to server")
  }
}

export { ApiError }
