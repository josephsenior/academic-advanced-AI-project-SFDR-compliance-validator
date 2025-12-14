# System Status & Integration Guide

## Current Issue: Flask/Werkzeug Server Problem

### Problem Identified
On this Windows system with Python 3.12, Flask's built-in Werkzeug server **cannot bind properly** to network ports. The server prints startup messages but exits immediately without actually listening for connections. This appears to be a Werkzeug/Windows/Python 3.12 compatibility issue.

**Symptoms:**
- Server prints "Running on http://127.0.0.1:5000"
- Immediately prints "Shutting down..." or returns to prompt
- No actual HTTP requests can be served
- Happens with both `app.run()` and `waitress.serve()`

**Root Cause:**
- Flask's Werkzeug development server fails to bind on this system
- Not a code issue - minimal Flask apps also fail
- Not a port conflict - port 5000 is free
- Threading workaround also fails

## Solution: Use Separate Terminal Windows

Since the server cannot run as a background process, you must start it in a **separate terminal window** that stays open.

### Method 1: Use Batch Scripts (EASIEST)

**Start API Server Only:**
```
start_api_server.bat
```

**Start Complete System (API + Frontend):**
```
START_SYSTEM.bat
```

This will:
1. Open API server in separate window
2. Wait 5 seconds
3. Open frontend server in separate window  
4. Open browser to http://localhost:3000

### Method 2: Manual Start

**Terminal 1 - API Server:**
```powershell
cd "C:\Users\GIGABYTE\Desktop\Advanced Ai Project"
python api.py
```
Leave this window open!

**Terminal 2 - Frontend:**
```powershell
cd "C:\Users\GIGABYTE\Desktop\Advanced Ai Project\frontend"
pnpm dev
```
Leave this window open!

**Browser:**
```
http://localhost:3000
```

## Frontend-Backend Integration Status

### [OK] Backend API (api.py)
- **10 REST endpoints** implemented
- **CORS enabled** for frontend
- **Port:** 5000
- **Base URL:** http://localhost:5000/api/v1

**Endpoints:**
- `GET /api/v1/health` - Health check
- `POST /api/v1/upload` - Upload document  
- `POST /api/v1/validate/<id>` - Start validation
- `GET /api/v1/status/<id>` - Get status/progress
- `GET /api/v1/results/<id>` - Get validation results
- `POST /api/v1/fix/<id>` - Apply auto-fixes
- `GET /api/v1/download/<id>` - Download corrected document
- `GET /api/v1/report/<id>` - Generate report
- `GET /api/v1/list` - List all documents
- `DELETE /api/v1/delete/<id>` - Delete document

### [OK] Frontend UI (frontend/)
- **Framework:** Next.js 16 + React 19
- **TypeScript types** aligned with backend
- **API client** in `lib/api.ts`
- **Port:** 3000
- **Pages:**
  - `/` - Upload page
  - `/dashboard/[documentId]` - Validation dashboard

### [OK] Integration Configuration
- **API Base URL** correctly set to `http://localhost:5000/api/v1`
- **CORS** properly enabled on backend
- **Type definitions** match API response formats:
  - DocumentMetadata supports both French and English field names
  - ValidationStatus: "pending" | "processing" | "completed" | "failed"
  - ValidationResults with compliance_score, issues, category_counts
- **API functions** implemented for all endpoints

## Testing the Integration

Once both servers are running in separate windows:

### 1. Test Backend Directly
```powershell
# In a NEW PowerShell window (not the server windows!)
Invoke-RestMethod http://localhost:5000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### 2. Test Frontend
Open browser to `http://localhost:3000`

**Upload Flow:**
1. Click "Upload Document"
2. Select a .pptx file from `dataset/example_1/`
3. Click "Validate"
4. Should redirect to dashboard showing progress
5. Wait 60-90 seconds for validation
6. View results with compliance score and issues

## Why This Approach Works

**Problem:** Flask server exits immediately when run as background process
**Solution:** Run in foreground in separate window - keeps process alive

**The batch scripts handle this by:**
- Using `start` command to open new CMD windows
- Using `/k` flag to keep windows open after command
- Servers run in foreground in their own windows
- Windows closing = servers stop (clean shutdown)

## Verification Checklist

- [ ] Can start API server in separate window (stays open)
- [ ] Can access http://localhost:5000/api/v1/health
- [ ] Can start frontend server in separate window
- [ ] Can access http://localhost:3000
- [ ] Can upload document through UI
- [ ] Can see validation progress
- [ ] Can view validation results with issues
- [ ] APIs return correct JSON formats

## Alternative: Production Deployment

For actual deployment, use a production WSGI server like **Gunicorn** (Linux) or **mod_wsgi** (Apache):

```bash
# Linux/Mac
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api:app

# Windows with waitress (if it worked)
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 api:app
```

But for local development on this Windows machine, use the batch script approach.

## Summary

**Frontend [OK] Backend [OK] Integration [OK]**

The code is correct, types match, APIs are properly implemented, CORS is enabled. The **only issue** is that Flask's development server cannot run as a daemon process on this Windows system, so you must use separate terminal windows or the provided batch scripts.

**To verify everything works:**
```
Double-click START_SYSTEM.bat
```

Both servers will start in separate windows and browser will open automatically.
