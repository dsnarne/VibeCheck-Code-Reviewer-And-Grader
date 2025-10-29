#!/bin/bash
# Quick test to check backend file endpoints

echo "🔍 Testing Backend File Endpoints"
echo "=================================="
echo ""

# Test 1: Check if backend is running
echo "1️⃣ Checking if backend is running..."
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "   ✅ Backend is running"
else
    echo "   ❌ Backend is NOT running"
    exit 1
fi

# Test 2: Get latest repo
echo ""
echo "2️⃣ Getting latest repository..."
response=$(curl -s "http://localhost:8000/api/repos?limit=1")

if echo "$response" | grep -q "error"; then
    echo "   ❌ Error getting repos: $response"
    exit 1
fi

repo_id=$(echo "$response" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "   Found repo_id: $repo_id"

if [ -z "$repo_id" ]; then
    echo "   ❌ No repositories found. You need to analyze a repo first!"
    exit 1
fi

# Test 3: Check if repo has files
echo ""
echo "3️⃣ Checking file metadata..."
scoring=$(curl -s "http://localhost:8000/api/repos/$repo_id/scoring")

file_count=$(echo "$scoring" | grep -o '"file_count":[0-9]*' | grep -o '[0-9]*')
echo "   File count from database: $file_count"

if [ -z "$file_count" ] || [ "$file_count" = "0" ]; then
    echo "   ❌ NO FILES STORED!"
    echo "   This is why file viewer is failing."
    echo ""
    echo "💡 Files need to be uploaded during analysis."
    echo "   Check the analysis endpoint logs for errors."
    exit 0
fi

# Test 4: Try to get files list
echo ""
echo "4️⃣ Getting files list..."
files=$(echo "$scoring" | grep -o '"files":\[.*\]' | cut -d'[' -f2- | cut -d']' -f1)

if [ -n "$files" ]; then
    echo "   ✅ Files array found in scoring"
    echo "$files" | head -c 200
    echo "..."
else
    echo "   ❌ No files array in scoring response"
fi

echo ""
echo "=================================="
echo "✅ Test Complete"
