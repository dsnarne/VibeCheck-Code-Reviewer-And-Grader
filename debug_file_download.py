#!/usr/bin/env python3
"""Test script to debug file loading issue"""

import sys
import json
sys.path.append('Backend')

from core.services.supabase import supabase
import httpx

def test_file_download():
    """Test the file download flow"""
    print("=" * 70)
    print("DEBUGGING FILE LOADING ISSUE")
    print("=" * 70)
    
    if not supabase:
        print("\n❌ Supabase not configured")
        print("Check your .env file for SUPABASE_URL and SUPABASE_ANON_KEY")
        return
    
    print("\n1️⃣ Checking repositories in database...")
    
    # Get latest repository
    result = supabase.table("repos").select("*").order("created_at", desc=True).limit(1).execute()
    
    if not result.data:
        print("❌ No repositories found in database")
        print("\n💡 You need to analyze a repository first!")
        return
    
    repo = result.data[0]
    repo_id = repo.get('id')
    repo_name = repo.get('repo_name', 'Unknown')
    
    print(f"✓ Found repository: {repo_name}")
    print(f"  ID: {repo_id}")
    print(f"  Files stored: {repo.get('files_ready_for_embedding', False)}")
    print(f"  File count: {repo.get('file_count', 0)}")
    
    file_metadata = repo.get('file_metadata', [])
    print(f"  File metadata entries: {len(file_metadata)}")
    
    if not file_metadata:
        print("\n❌ NO FILES IN METADATA!")
        print("   Files were not stored during analysis.")
        print("   This is why the file viewer is failing.")
        return
    
    print(f"\n2️⃣ First 10 files in metadata:")
    for i, file in enumerate(file_metadata[:10], 1):
        rel = file.get('relative_path', 'N/A')
        name = file.get('name', 'N/A')
        storage = file.get('storage_path', 'N/A')
        print(f"  [{i}] name='{name}' relative_path='{rel}' storage_path='{storage}'")
    
    print(f"\n3️⃣ Testing file download endpoint...")
    
    # Try to get one file
    if file_metadata:
        test_file = file_metadata[0]
        test_path = test_file.get('relative_path') or test_file.get('name')
        
        print(f"  Testing with: {test_path}")
        
        try:
            url = f"http://localhost:8000/api/files/repos/{repo_id}/file/{test_path}"
            print(f"  URL: {url}")
            
            with httpx.Client() as client:
                response = client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✅ SUCCESS! Got {len(data.get('content', ''))} bytes")
                else:
                    print(f"  ❌ FAILED: {response.status_code}")
                    print(f"  Error: {response.text}")
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
    
    print(f"\n4️⃣ Testing scoring endpoint...")
    try:
        url = f"http://localhost:8000/api/repos/{repo_id}/scoring"
        
        with httpx.Client() as client:
            response = client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                files = data.get('files', [])
                print(f"  ✅ Got scoring with {len(files)} files")
                
                if files:
                    print(f"\n  First file from scoring:")
                    print(f"  name='{files[0].get('name')}' path='{files[0].get('path')}'")
            else:
                print(f"  ❌ FAILED: {response.status_code}")
                print(f"  Error: {response.text}")
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
    
    print("\n" + "=" * 70)
    print("DEBUGGING COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    test_file_download()
