#!/usr/bin/env python3
"""
Quick test script for the file viewer functionality
"""

import sys
sys.path.append('Backend')
import requests
import json

def test_file_endpoint():
    """Test the file content endpoint"""
    
    # You need to provide a real repo_id and file path
    print("=" * 60)
    print("TESTING FILE DOWNLOAD ENDPOINT")
    print("=" * 60)
    
    # For now, let's just test the endpoint structure
    print("\n1. First, analyze a repository to get a repo_id:")
    print("   POST http://localhost:8000/api/repos/analyze")
    print("   Body: {")
    print('     "repo_url": "https://github.com/dsnarne/dashcam-following-distance-driver-safety"')
    print('     "user_id": "test-user"')
    print("   }")
    
    print("\n2. Then get scoring to see files:")
    print("   GET http://localhost:8000/api/repos/{repo_id}/scoring")
    
    print("\n3. Finally, try to get a file:")
    print("   GET http://localhost:8000/api/files/repos/{repo_id}/file/{file_path}")
    
    print("\n" + "=" * 60)
    print("EASIER: Test in Browser!")
    print("=" * 60)
    print("\n1. Open http://localhost:5175 in your browser")
    print("2. Open DevTools (F12)")
    print("3. Go to Console tab")
    print("4. Enter a repository URL")
    print("5. Click 'Analyze Repository'")
    print("6. Scroll to 'File Analysis'")
    print("7. Click 'View File' on any file")
    print("8. Check the console for logs!")
    
    print("\n" + "=" * 60)
    print("Backend is running on: http://localhost:8000")
    print("Frontend is running on: http://localhost:5175")
    print("=" * 60)

if __name__ == "__main__":
    test_file_endpoint()
