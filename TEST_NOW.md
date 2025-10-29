# 🧪 TESTING GUIDE - File Viewer

## ✅ Setup Status
- Backend: Running on http://localhost:8000
- Frontend: Open at http://localhost:5175

## 🚀 Test Steps

### Step 1: Open Browser Console
1. In your browser at http://localhost:5175
2. Press **F12** (or Cmd+Option+I on Mac)
3. Click the **"Console"** tab

### Step 2: Refresh the Page
1. Press **Ctrl+R** (or Cmd+R on Mac) to refresh
2. This loads the latest frontend code with new logging

### Step 3: Analyze a Repository
1. Enter this repository URL:
   ```
   https://github.com/dsnarne/dashcam-following-distance-driver-safety
   ```
2. Click **"Analyze Repository"**
3. Wait for analysis to complete (you'll see the scores appear)

### Step 4: Test File Viewer
1. Scroll down to the **"File Analysis"** section
2. You should see a list of files with "View File" buttons
3. Click **"View File"** on any file
4. Watch the console for logs

### Step 5: Check Console Output
Look for messages like:
```
Fetching file: {repoId: "...", filePath: "..."}
File object: {name: "...", path: "...", ...}
Using file path: "..."
```

### Step 6: Check Backend Terminal
1. Look at the terminal where you ran `uvicorn`
2. You should see backend logs like:
   ```
   INFO: Looking for file_path: ...
   INFO: Available files in metadata (X total):
   INFO:   - relative_path: ...
   ```

## 📋 What to Report Back

Please tell me:
1. **What appears in the browser console?** (Copy the messages)
2. **What appears in the backend terminal?** (Copy the messages)
3. **Does the modal appear?** (Yes/No)
4. **Any error messages?**

## 🔍 If It Still Fails

The logs will show us:
- What file path is being requested from frontend
- What file paths are available in the backend
- Exactly why the matching fails

Then I can fix it!
