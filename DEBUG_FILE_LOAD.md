# 🔍 Debugging File Load Issue

## Problem
Frontend says "Failed to load file content" when clicking "View File"

## Steps to Debug

### 1. Check Browser Console
Open browser developer tools and look for:
- The console.log messages showing `repoId` and `filePath`
- Error messages with details about what failed

### 2. Check What Files Are Available
The files may not be stored in Supabase yet, or the path format might be incorrect.

### 3. Check Backend Logs
Look at the backend terminal for errors when you click "View File"

## Common Issues:

### Issue 1: No files in Supabase
**Symptoms:** "File not found in repository" or "No file storage path found"

**Solution:** 
1. Analyze a repository first
2. Make sure `file_storage_base_path` starts with `repos/`
3. Verify files were uploaded successfully during analysis

### Issue 2: Wrong path format
**Symptoms:** "File storage path not found"

**Solution:**
The `file_path` should match the `relative_path` in file_metadata, e.g.:
- `src/app.py`
- `requirements.txt`

Not:
- `/src/app.py`
- `repos/{repo_id}/src/app.py`

### Issue 3: Storage path mismatch
**Symptoms:** "Could not download file from storage"

**Solution:**
The storage_path in file_metadata should match what's in Supabase storage.
Check if `storage_path` field exists in the database for each file.

## How to Test:

1. Open http://localhost:5175
2. Open browser DevTools (F12)
3. Go to Console tab
4. Click "View File" on any file
5. Look at the console messages

## Expected Console Output:
```
Fetching file: {repoId: "abc-123", filePath: "src/app.py"}
File data received: {path: "src/app.py", content: "...", file_info: {...}}
```

If you see an error instead, copy the error message and check backend logs.
