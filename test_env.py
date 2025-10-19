#!/usr/bin/env python3
"""
Test script to check environment variables and ChatGPT connection.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from backend directory
load_dotenv(os.path.join(os.path.dirname(__file__), 'backend', '.env'))

print("=== Environment Variables Test ===")
print()

# Check OpenAI API key
openai_key = os.getenv("OPENAI_API_KEY")
print(f"OPENAI_API_KEY: {'Present' if openai_key else 'Missing'}")
if openai_key:
    print(f"  Key preview: {openai_key[:8]}...{openai_key[-4:] if len(openai_key) > 12 else '***'}")
print()

# Check GitHub credentials
github_token = os.getenv("GITHUB_TOKEN")
github_app_id = os.getenv("GITHUB_APP_ID")
github_app_private_key = os.getenv("GITHUB_APP_PRIVATE_KEY")
github_app_installation_id = os.getenv("GITHUB_APP_INSTALLATION_ID")

print("GitHub credentials:")
print(f"  GITHUB_TOKEN: {'Present' if github_token else 'Missing'}")
print(f"  GITHUB_APP_ID: {'Present' if github_app_id else 'Missing'}")
print(f"  GITHUB_APP_PRIVATE_KEY: {'Present' if github_app_private_key else 'Missing'}")
print(f"  GITHUB_APP_INSTALLATION_ID: {'Present' if github_app_installation_id else 'Missing'}")
print()

# Check Supabase credentials
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")

print("Supabase credentials:")
print(f"  SUPABASE_URL: {'Present' if supabase_url else 'Missing'}")
print(f"  SUPABASE_ANON_KEY: {'Present' if supabase_key else 'Missing'}")
print()

# List all environment variables that start with common prefixes
print("All environment variables with common prefixes:")
for key, value in os.environ.items():
    if any(key.startswith(prefix) for prefix in ['OPENAI', 'GITHUB', 'SUPABASE']):
        if 'KEY' in key or 'TOKEN' in key or 'PRIVATE' in key:
            print(f"  {key}: {'Present' if value else 'Missing'}")
        else:
            print(f"  {key}: {value}")
print()

print("=== Test completed ===")
