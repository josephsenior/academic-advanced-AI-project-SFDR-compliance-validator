# Complete UI Integration Guide

## ✅ REST API Ready!

Your backend REST API is now complete with 10 endpoints covering the entire validation workflow.

**API Server**: `api.py`  
**Documentation**: `API_DOCUMENTATION.md`  
**Test Script**: `test_api.py`

---

## 🎨 V0.DEV PROMPT - Copy & Paste This

```
Create a professional compliance validation dashboard for financial document analysis. This connects to an existing REST API.

API ENDPOINTS (Base URL: http://localhost:5000/api/v1):
- POST /upload - Upload document (multipart/form-data)
- POST /validate/<id> - Start validation  
- GET /status/<id> - Get validation status
- GET /results/<id> - Get validation results
- POST /fix/<id> - Apply auto-fixes
- GET /download/<id>?type=corrected - Download corrected document
- GET /list - List all documents
- DELETE /delete/<id> - Delete document

PAGES NEEDED:

1. UPLOAD PAGE (/)
   - Hero section with title: "Document Compliance Validator"
   - Drag & drop zone (accept .pptx, .pdf, .docx)
   - File list with upload progress bars
   - Optional metadata form:
     * Société de Gestion (text input)
     * Client Type (toggle: Professional / Non-Professional)
     * New Strategy? (checkbox)
     * New Product? (checkbox)
   - "Start Validation" button → navigates to /dashboard/:documentId
   - Recent validations list (fetch from /api/v1/list)

2. DASHBOARD PAGE (/dashboard/:documentId)
   - Header with document filename and status badge
   - Real-time status updates (poll /api/v1/status every 2s)
   - Progress bar showing: Uploading → Extracting → Validating → Complete
   
   - Top Metrics Row (4 cards):
     * Compliance Score (circular progress, 0-100%)
     * Total Issues (number with color)
     * Status (Pass/Warning/Error badge)
     * Quick Actions (Export, Download, Delete buttons)
   
   - Main Content (2-column layout):
     LEFT SIDEBAR (30%):
       - Category Filter (collapsible sections):
         * ESG Compliance (red, count badge)
         * Performance Rules (orange, count badge)
         * Structure Issues (blue, count badge)
         * Disclaimers (yellow, count badge)
         * Registration (purple, count badge)
         * Data Consistency (green, count badge)
         * Other (gray, count badge)
       
       - Severity Filter (checkboxes):
         * Critical (red icon)
         * High (orange icon)
         * Medium (yellow icon)
         * Low (gray icon)
       
       - Slide Navigator:
         * Mini thumbnails with issue dots
         * Click to filter by slide
     
     CENTER PANEL (70%):
       - Search bar (search issues by keyword)
       - Sort dropdown (Severity / Location / Category)
       - Issues list (virtualized for performance):
         
         ISSUE CARD DESIGN:
         ┌─────────────────────────────────────┐
         │ [🔴 CRITICAL]  ESG Compliance        │
         │                                      │
         │ Article 8 fund exceeds 10% ESG limit │
         │ Location: Slides 3, 5, 7             │
         │                                      │
         │ [View Details ▼]                     │
         │                                      │
         │ ▼ EXPANDED:                          │
         │   Context: "Total ESG text: 15.3%..." │
         │   Suggestion: "Reduce to below 10%"  │
         │   Rule: Section 4.1 - ESG Compliance │
         │                                      │
         │   [Apply Fix] (if auto_fixable)      │
         │   [Mark as Reviewed] [Ignore]        │
         └─────────────────────────────────────┘
       
       - Empty state when no issues:
         "🎉 No issues found! Compliance score: 100%"

3. STATISTICS TABLE (below issues):
   - Tables Checked: X
   - Tables with Source/Date: X
   - Charts Analyzed: X  
   - Numerical Values Checked: X
   - Values Matching Reference: X

FEATURES:
- Real-time validation progress (WebSocket or polling)
- Filter issues by severity, category, slide
- Search issues by keyword
- Sort issues (severity, location, category)
- Expandable issue details
- Apply fixes button (POST /api/v1/fix/:id)
- Download corrected document
- Export report (PDF/JSON)
- Delete document
- Toast notifications for actions
- Loading states (skeleton screens)
- Error handling with retry
- Dark mode toggle
- Keyboard shortcuts (? for help, / for search, esc to close modals)

DESIGN SYSTEM:
- Modern financial SaaS aesthetic (like Stripe, Linear, Notion)
- Color palette:
  * Primary: Indigo/Purple (#8B5CF6)
  * Critical: Red (#EF4444)
  * High: Orange (#F59E0B)
  * Medium: Yellow (#EAB308)
  * Low: Gray (#6B7280)
  * Success: Green (#10B981)
- Typography: Inter or System UI font
- Smooth transitions (200-300ms)
- Subtle shadows and borders
- Micro-interactions on hover/click
- Responsive (desktop-first, but works on tablet)

TECH STACK:
- React 18 + TypeScript
- Vite (build tool)
- Tailwind CSS + shadcn/ui components
- TanStack Query (data fetching, caching)
- Zustand (state management)
- React Router (navigation)
- Lucide React (icons)
- Recharts (compliance score gauge)
- @tanstack/react-virtual (virtualize long issue lists)
- Framer Motion (animations)

STATE MANAGEMENT:
- Use TanStack Query for API calls:
  * useQuery for fetching status/results
  * useMutation for upload/validate/fix/delete
  * Automatic refetching on window focus
  * Optimistic updates
- Use Zustand for UI state (filters, search, dark mode)

API INTEGRATION:
```typescript
const API_BASE = 'http://localhost:5000/api/v1';

// Upload document
const uploadDocument = async (file: File, metadata: any) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('metadata', JSON.stringify(metadata));
  
  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData
  });
  
  if (!response.ok) throw new Error('Upload failed');
  return response.json();
};

// Start validation
const validateDocument = async (documentId: string, options: any) => {
  const response = await fetch(`${API_BASE}/validate/${documentId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(options)
  });
  
  if (!response.ok) throw new Error('Validation failed');
  return response.json();
};

// Get results
const getResults = async (documentId: string, filters?: any) => {
  const params = new URLSearchParams(filters);
  const response = await fetch(`${API_BASE}/results/${documentId}?${params}`);
  
  if (!response.ok) throw new Error('Failed to fetch results');
  return response.json();
};
```

EXAMPLE DATA STRUCTURE (from API):
```json
{
  "document_id": "abc-123",
  "overall_status": "error",
  "compliance_score": 67,
  "total_issues": 14,
  "issues_by_severity": {
    "critical": 2,
    "high": 5,
    "medium": 4,
    "low": 3
  },
  "issues_by_category": {
    "esg": [
      {
        "issue_type": "esg_overmentioned_article8",
        "severity": "critical",
        "category": "esg",
        "location": "Slides 3, 5, 7",
        "slide_number": 3,
        "message": "Article 8 fund exceeds 10% ESG limit (15.3% found)",
        "context": "Total ESG text: 4821 chars...",
        "suggestion": "Reduce ESG content to below 10%",
        "auto_fixable": false,
        "rule_reference": "Section 4.1 - ESG Compliance"
      }
    ]
  },
  "statistics": {
    "total_tables_checked": 59,
    "tables_with_source_date": 45,
    "total_charts_analyzed": 52
  }
}
```

ROUTING:
- / - Upload page
- /dashboard/:documentId - Dashboard with results
- /list - Recent validations list

COMPONENTS TO BUILD:
- UploadZone (drag & drop)
- MetadataForm (optional inputs)
- ProgressBar (upload/validation progress)
- ComplianceScoreGauge (circular progress)
- IssueCard (collapsible issue details)
- CategoryFilter (sidebar filters)
- SeverityBadge (colored badges)
- SlideNavigator (thumbnail grid)
- StatisticsTable (validation stats)
- ActionButtons (export, download, delete)

REQUIREMENTS:
- Production-ready code
- Type-safe (TypeScript)
- Accessible (ARIA labels, keyboard navigation)
- Performant (virtualization for long lists)
- Beautiful UI with smooth animations
- Proper error handling
- Loading states
- Empty states
- Toast notifications

Make it look like a premium SaaS product. Focus on clarity, ease of use, and professional aesthetics.
```

---

## 🚀 INTEGRATION STEPS

### Step 1: Generate UI with v0.dev
1. Go to https://v0.dev
2. Paste the prompt above
3. v0 will generate the React components
4. Download the generated code

### Step 2: Setup Project
```bash
# In a new folder (e.g., frontend/)
npm create vite@latest . -- --template react-ts
npm install

# Install dependencies
npm install @tanstack/react-query @tanstack/react-virtual
npm install zustand react-router-dom
npm install lucide-react recharts
npm install framer-motion
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Install shadcn/ui
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card input badge progress dropdown-menu
```

### Step 3: Start Both Servers
```bash
# Terminal 1: Backend API
cd "C:\Users\GIGABYTE\Desktop\Advanced Ai Project"
python api.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

### Step 4: Connect Frontend to Backend
Update `vite.config.ts`:
```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
})
```

---

## 📋 TESTING CHECKLIST

Once UI is generated:
- [ ] Upload a document
- [ ] See upload progress
- [ ] Start validation
- [ ] Watch real-time progress updates
- [ ] View validation results
- [ ] Filter by severity/category
- [ ] Search issues
- [ ] Expand issue details
- [ ] Apply auto-fixes
- [ ] Download corrected document
- [ ] Export report
- [ ] Delete document
- [ ] Dark mode toggle
- [ ] Test keyboard shortcuts

---

## 🎯 NEXT STEPS

1. **Copy the v0 prompt above** and paste it into https://v0.dev
2. **Generate the UI** (v0 will create all components)
3. **Download** the generated code
4. **Install dependencies** as shown in Step 2
5. **Start the backend**: `python api.py`
6. **Start the frontend**: `npm run dev`
7. **Test the flow**: Upload → Validate → View Results → Fix → Download

The backend API is **production-ready** with:
- ✅ 10 REST endpoints
- ✅ File upload handling
- ✅ Validation pipeline integration
- ✅ Error handling
- ✅ CORS enabled
- ✅ Status tracking
- ✅ Result filtering
- ✅ Document correction
- ✅ Report generation
- ✅ Complete documentation

**All you need now is to generate the frontend UI with v0.dev using the prompt above!**
