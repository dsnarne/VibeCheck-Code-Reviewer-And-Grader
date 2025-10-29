#!/usr/bin/env python3
"""Test script to check what files are actually in the database"""

import sys
sys.path.append('Backend')

from core.services.supabase import supabase
import json

def check_files():
    if not supabase:
        print("Supabase not configured")
        return
    
    # Get latest repository
    result = supabase.table("repos").select("*").order("created_at", desc=True).limit(1).execute()
    
    if not result.data:
        print("No repositories found")
        return
    
    repo = result.data[0]
    print(f"\nRepository: {repo.get('repo_name')}")
    print(f"ID: {repo.get('id')}")
    print(f"File metadata count: {len(repo.get('file_metadata', []))}")
    
    print(f"\nFirst 10 files in metadata:")
    for i, file in enumerate(repo.get('file_metadata', [])[:10]):
        print(f"\n[{i+1}]")
        print(f"  relative_path: {file.get('relative_path')}")
        print(f"  path: {file.get('path')}")
        print(f"  name: {file.get('name')}")
        print(f"  storage_path: {file.get('storage_path')}")

if __name__ == "__main__":
    check_files()
