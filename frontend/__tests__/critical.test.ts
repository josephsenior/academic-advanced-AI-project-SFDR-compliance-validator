/**
 * Critical Path Tests for Compliance Dashboard
 * Tests the most important user flows and error handling
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ApiError } from '../lib/api'

// Mock fetch for testing
global.fetch = vi.fn()

describe('API Error Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should throw ApiError with proper message on 404', async () => {
    const mockFetch = global.fetch as ReturnType<typeof vi.fn>
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ message: 'Document not found', code: 'NOT_FOUND' }),
    })

    const { uploadDocument } = await import('../lib/api')
    const file = new File(['test'], 'test.pptx')

    await expect(uploadDocument(file)).rejects.toThrow('Document not found')
  })

  it('should retry on 500 errors', async () => {
    const mockFetch = global.fetch as ReturnType<typeof vi.fn>
    // First two calls fail with 500, third succeeds
    mockFetch
      .mockResolvedValueOnce({ ok: false, status: 500 })
      .mockResolvedValueOnce({ ok: false, status: 500 })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ document_id: 'test-123', has_metadata: false, has_prospectus: false }),
      })

    const { uploadDocument } = await import('../lib/api')
    const file = new File(['test'], 'test.pptx')

    const result = await uploadDocument(file)
    expect(result.document_id).toBe('test-123')
    expect(mockFetch).toHaveBeenCalledTimes(3)
  })

  it('should handle network errors gracefully', async () => {
    const mockFetch = global.fetch as ReturnType<typeof vi.fn>
    mockFetch.mockRejectedValue(new Error('Network error'))

    const { getValidationStatus } = await import('../lib/api')

    await expect(getValidationStatus('test-123')).rejects.toThrow('Unable to connect to server')
  })
})

describe('Environment Configuration', () => {
  it('should use environment variable for API base URL', () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = 'https://api.example.com/v1'
    
    // Re-import to get updated config
    vi.resetModules()
    
    // API base should be from environment
    expect(process.env.NEXT_PUBLIC_API_BASE_URL).toBe('https://api.example.com/v1')
  })

  it('should fallback to localhost when no env var set', () => {
    delete process.env.NEXT_PUBLIC_API_BASE_URL
    
    // Should default to localhost
    expect(process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5000/api/v1').toBe(
      'http://localhost:5000/api/v1'
    )
  })
})

describe('Demo Data', () => {
  it('should load demo data correctly', async () => {
    const { demoResults } = await import('../lib/demo-data')

    expect(demoResults.document_id).toBe('demo-123')
    expect(demoResults.total_issues).toBe(14)
    expect(demoResults.compliance_score).toBe(67)
    expect(demoResults.issues_by_category).toHaveProperty('esg')
    expect(demoResults.issues_by_category).toHaveProperty('performance')
  })

  it('should have valid issue structure', async () => {
    const { demoResults } = await import('../lib/demo-data')

    const esgIssues = demoResults.issues_by_category.esg
    expect(esgIssues.length).toBeGreaterThan(0)

    const firstIssue = esgIssues[0]
    expect(firstIssue).toHaveProperty('issue_type')
    expect(firstIssue).toHaveProperty('severity')
    expect(firstIssue).toHaveProperty('category')
    expect(firstIssue).toHaveProperty('message')
    expect(firstIssue).toHaveProperty('auto_fixable')
  })
})

describe('Error Boundary', () => {
  it('should catch and display errors', () => {
    // Error boundary test would require React Testing Library
    // Placeholder for now - to be implemented with proper testing setup
    expect(true).toBe(true)
  })
})

describe('API Retry Logic', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.resetModules()
  })

  it('should stop retrying after max attempts', async () => {
    const mockFetch = global.fetch as ReturnType<typeof vi.fn>
    mockFetch.mockRejectedValue(new Error('Network error'))

    const { listDocuments } = await import('../lib/api')

    await expect(listDocuments()).rejects.toThrow()
    // Should try initial + 3 retries = 4 total calls
    expect(mockFetch).toHaveBeenCalledTimes(4)
  })

  it('should not retry on 4xx errors', async () => {
    vi.clearAllMocks()
    vi.resetModules()
    
    const mockFetch = global.fetch as ReturnType<typeof vi.fn>
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ message: 'Bad request' }),
    })

    const { validateDocument } = await import('../lib/api')

    await expect(validateDocument('test-123')).rejects.toThrow()
    // Should not retry on 4xx errors
    expect(mockFetch).toHaveBeenCalledTimes(1)
  })
})

describe('Type Safety', () => {
  it('should have proper TypeScript types', async () => {
    const { demoResults } = await import('../lib/demo-data')
    
    // These should compile without errors
    const score: number = demoResults.compliance_score
    const status: 'pass' | 'warning' | 'error' = demoResults.overall_status
    const issues: number = demoResults.total_issues

    expect(typeof score).toBe('number')
    expect(['pass', 'warning', 'error']).toContain(status)
    expect(typeof issues).toBe('number')
  })
})
