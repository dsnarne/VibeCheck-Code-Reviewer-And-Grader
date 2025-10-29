#!/bin/bash

echo "🧪 Testing File List Display"
echo "============================"
echo ""

# Get the repository ID
echo "1️⃣ Getting repository data..."
RESPONSE=$(curl -s "http://localhost:8000/api/repos")

# Check if we have a valid response
if echo "$RESPONSE" | grep -q "Not Found"; then
    echo "   ❌ No repositories found"
    echo ""
    echo "   Please analyze a repository first at http://localhost:5173"
    exit 1
fi

# We need to get scoring data to see what files are returned
echo "✅ Can access repository data"
echo ""

echo "2️⃣ Testing scoring endpoint for files..."
# This would need the actual repo_id from above
# For now let's just show what we know

cd /Users/dhirennarne/Desktop/VibeCheck-Code-Reviewer-And-Grader && source venv/bin/activate && python3 << 'EOF'
from Backend.core.services.supabase import supabase

# Get latest repo
result = supabase.table('repos').select('*').order('created_at', desc=True).limit(1).execute()

if result.data:
    repo = result.data[0]
    repo_id = repo['id']
    
    print(f"Found repository: {repo_id}")
    print(f"Files in metadata: {len(repo.get('file_metadata', []))}")
    
    # Get scoring to see what files are returned
    import httpx
    scoring_response = httpx.get(f'http://localhost:8000/api/repos/{repo_id}/scoring').json()
    
    files = scoring_response.get('files', [])
    print(f"Files in scoring response: {len(files)}")
    
    if files:
        print("\nFirst 10 files from scoring:")
        for i, file in enumerate(files[:10], 1):
            print(f"  {i}. {file.get('name')} - {file.get('path')}")
    else:
        print("\n❌ NO FILES IN SCORING RESPONSE!")
        print("   This is why FileList is empty")
        print("\n   Checking if file_metadata is being passed to scoring endpoint...")
EOF

echo ""
echo "✅ Test complete!"
