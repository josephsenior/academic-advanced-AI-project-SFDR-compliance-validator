# 🚀 Quick Start Guide - Compliance Dashboard

## ✅ Setup Complete!

Your UI is ready to connect to the backend API. Follow these steps:

## Step 1: Start the Backend API

Open a terminal and run:
```bash
cd "C:\Users\GIGABYTE\Desktop\Advanced Ai Project"
python api.py
```

You should see:
```
================================================================================
🚀 Document Validation API Server
================================================================================
Server running on http://localhost:5000
```

## Step 2: Start the Frontend

Open a **NEW** terminal and run:
```bash
cd "C:\Users\GIGABYTE\Desktop\Advanced Ai Project\compliance-dashboard"
pnpm install  # If you haven't already
pnpm dev
```

The UI will start on `http://localhost:3000`

## Step 3: Test the Integration

1. **Open browser**: http://localhost:3000
2. **Upload a document**: Drag & drop a .pptx file
3. **Fill metadata** (optional):
   - Société de Gestion: `ODDO BHF ASSET MANAGEMENT SAS`
   - Client Type: `Non-Professional`
4. **Click "Start Validation"**
5. **Watch progress**: Uploading → Extracting → Validating → Complete
6. **View results**: Issues categorized by severity and category

## 📁 Test with Example Document

Use one of the example documents from the dataset:
```
C:\Users\GIGABYTE\Desktop\Advanced Ai Project\dataset\example_1\
```

## 🎨 UI Features

✅ **Upload Page**
- Drag & drop file upload
- Optional metadata form
- Recent validations list
- Dark mode toggle

✅ **Dashboard Page**
- Real-time validation progress
- Compliance score gauge (0-100%)
- Issue browser with filters
- Category filters (ESG, Performance, Structure, etc.)
- Severity filters (Critical, High, Medium, Low)
- Searchable, sortable issues
- Expandable issue details
- Apply fixes button
- Download corrected document
- Export report

## 🔧 Configuration

### Backend API
- **URL**: `http://localhost:5000/api/v1`
- **Config**: `compliance-dashboard/lib/api.ts`
- **CORS**: Already enabled in `api.py`

### Frontend
- **Port**: 3000 (default Next.js)
- **Config**: `compliance-dashboard/next.config.mjs`
- **Types**: `compliance-dashboard/lib/types.ts`

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 5000 is in use
netstat -ano | findstr :5000

# Kill process if needed
taskkill /PID <PID> /F

# Restart backend
python api.py
```

### Frontend shows "Failed to fetch"
1. Make sure backend is running on port 5000
2. Check CORS is enabled in `api.py` (already done)
3. Clear browser cache and refresh

### Upload fails
1. Check file type (.pptx, .pdf, .docx only)
2. Check file size (max 100MB)
3. Check backend terminal for errors

## 📊 What Happens During Validation

1. **Upload** (5-10s): File is uploaded to backend
2. **Extract** (30-60s): Document is parsed for content
   - Tables, charts, text extracted
   - Structure analyzed
   - Features identified
3. **Validate** (10-20s): Compliance checks run
   - ESG/SFDR rules
   - Performance rules
   - Structure validation
   - Disclaimer checks
   - Registration validation
   - Data consistency
4. **Results**: Issues displayed with:
   - Severity level
   - Category
   - Location (slide/page)
   - Context
   - Suggestion
   - Auto-fix availability

## 🎯 Example Workflow

```bash
# Terminal 1: Backend
cd "C:\Users\GIGABYTE\Desktop\Advanced Ai Project"
python api.py

# Terminal 2: Frontend  
cd "C:\Users\GIGABYTE\Desktop\Advanced Ai Project\compliance-dashboard"
pnpm dev

# Browser
# Open: http://localhost:3000
# Upload: dataset/example_1/ODDO BHF Active Small Cap_Product Presentation_4p_Mai 2024.pptx
# Wait: ~60 seconds for validation
# View: 10-20 compliance issues with detailed feedback
```

## 📋 Testing Checklist

- [ ] Backend API running on port 5000
- [ ] Frontend running on port 3000
- [ ] Can access http://localhost:3000
- [ ] Can upload a file
- [ ] See upload progress
- [ ] Navigate to dashboard
- [ ] See validation progress (Extracting → Validating)
- [ ] View results with compliance score
- [ ] Filter by severity (Critical/High/Medium/Low)
- [ ] Filter by category (ESG/Performance/etc.)
- [ ] Search issues
- [ ] Expand issue details
- [ ] See context and suggestions
- [ ] Toggle dark mode
- [ ] View statistics (tables/charts checked)

## 🚀 Next Steps

### Immediate
- Test with real documents
- Verify all filters work
- Check auto-fix functionality
- Test report export

### Production
- Add authentication
- Deploy backend (AWS/Azure/Heroku)
- Deploy frontend (Vercel/Netlify)
- Use PostgreSQL/Redis for job storage
- Add WebSocket for real-time updates
- Implement rate limiting
- Add monitoring (Sentry/Datadog)

## 📞 Need Help?

- **API Docs**: `API_DOCUMENTATION.md`
- **Backend Code**: `api.py`
- **Frontend Code**: `compliance-dashboard/`
- **Test Script**: `test_api.py`

---

**🎉 You're all set! Start both servers and open http://localhost:3000**
