#!/usr/bin/env python3
"""
Test script to debug file content loading
"""

import sys
sys.path.append('Backend')

from api_routes.file_content import get_file_content
import asyncio

async def test_file_download():
    print("Testing file content download...")
    
    # You'll need to provide a real repo_id and file_path
    # repo_id = input("Enter repo_id: ")
    # file_path = input("Enter file path: ")
    
    print("This script needs a real repository with stored files to test.")
    print("\nTo test manually:")
    print("1. Analyze a repository first")
    print("2. Note the repo_id from the response")
    print("3. Try calling the endpoint:")
    print("   curl http://localhost:8000/api/files/repos/{repo_id}/file/{file_path}")

if __name__ == "__main__":
    asyncio.run(test_file_download())
