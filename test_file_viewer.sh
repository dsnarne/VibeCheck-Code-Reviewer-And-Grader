#!/bin/bash
echo "🧪 Testing File Viewer..."
echo ""

echo "1️⃣ Testing backend API..."
response=$(curl -s http://localhost:8000/api/repos?limit=1)

if echo "$response" | grep -q "error"; then
    echo "   ❌ Error: $response"
    exit 1
fi

repo_id=$(echo "$response" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$repo_id" ]; then
    echo "   ⚠️  No repositories found yet"
    echo ""
    echo "   Next step: Analyze a repository first!"
    echo "   Go to http://localhost:5175"
    echo "   Enter: https://github.com/dsnarne/VibeCheck-Code-Reviewer-And-Grader"
    echo "   Click 'Analyze Repository'"
    exit 0
fi

echo "   ✅ Found repo_id: $repo_id"

echo ""
echo "2️⃣ Checking for files..."
scoring=$(curl -s "http://localhost:8000/api/repos/$repo_id/scoring")

file_count=$(echo "$scoring" | grep -o '"file_count":[0-9]*' | grep -o '[0-9]*')
echo "   File count: $file_count"

if [ -z "$file_count" ] || [ "$file_count" = "0" ]; then
    echo "   ⚠️  No files stored yet"
    echo ""
    echo "   This is why file viewer fails - files need to be uploaded during analysis"
    exit 0
fi

echo "   ✅ Files found in database"

echo ""
echo "3️⃣ Testing file endpoint with first file..."
files_array=$(echo "$scoring" | grep -o '"files":\[.*\]')

if echo "$files_array" | grep -q "src/example.py"; then
    echo "   ⚠️  Found mock file (src/example.py)"
    echo "   This is a placeholder - not a real file"
else
    # Get actual file path
    first_file=$(echo "$scoring" | grep -o '"path":"[^"]*"' | head -1 | cut -d'"' -f4)
    echo "   First file: $first_file"
    
    if [ -n "$first_file" ]; then
        echo "   Testing download..."
        result=$(curl -s "http://localhost:8000/api/files/repos/$repo_id/file/$first_file")
        
        if echo "$result" | grep -q "content"; then
            echo "   ✅ File download works!"
        else
            echo "   ❌ File download failed: $result"
        fi
    fi
fi

echo ""
echo "================================="
echo "✅ Test Complete"
echo ""
echo "💡 Next: Try the file viewer at http://localhost:5175"
