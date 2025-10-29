#!/usr/bin/env python3
"""Quick test to see what the issues API actually returns"""

import requests

# Test the issues endpoint
repo_id = input("Enter a repo_id from your database: ").strip()

if repo_id:
    try:
        # Test getting issues
        response = requests.get(f"http://localhost:8000/api/repos/{repo_id}/issues")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ API Response:")
            print(f"Total issues: {data.get('total_issues', 0)}")
            
            # Show issues by category
            for category, issues in data.get('issues', {}).items():
                if issues:
                    print(f"\n📁 {category.upper()} Issues ({len(issues)}):")
                    for i, issue in enumerate(issues[:3], 1):  # Show first 3
                        print(f"  {i}. {issue.get('file')}:{issue.get('line')}")
                        print(f"     Issue: {issue.get('issue')}")
                        print(f"     Code: {issue.get('codeSnippet', '')[:80]}...")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure:")
        print("1. Backend is running (uvicorn main:app --reload)")
        print("2. You have analyzed at least one repository")
        print("3. The repo_id is correct")

