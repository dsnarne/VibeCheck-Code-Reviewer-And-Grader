#!/usr/bin/env python3
"""
Debug script for ChatGPT analysis functionality.
Run this to test the ChatGPT API connection and see detailed logs.
"""

import sys
import os
import logging

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from core.services.chatgpt import test_chatgpt_connection, analyze_code_quality_with_chatgpt

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("=== ChatGPT Analysis Debug Script ===")
    print()
    
    # Test 1: API Connection
    print("1. Testing ChatGPT API connection...")
    connection_ok = test_chatgpt_connection()
    print(f"   Connection test: {'PASSED' if connection_ok else 'FAILED'}")
    print()
    
    if not connection_ok:
        print("❌ API connection failed. Please check:")
        print("   - OPENAI_API_KEY environment variable is set")
        print("   - API key is valid and has sufficient credits")
        print("   - Internet connection is working")
        return
    
    # Test 2: Sample Analysis
    print("2. Testing with sample analysis data...")
    
    # Create sample data
    sample_analysis_data = {
        "repo": "test-repo",
        "languages": {"Python": 1000, "JavaScript": 500},
        "team": {
            "giniContribution": 0.3,
            "topContributorsShare": 0.7,
            "contributions": [
                {"author": "user1", "netLines": 1000},
                {"author": "user2", "netLines": 500}
            ]
        },
        "commits": {
            "count": 50,
            "medianCompartmentalization": 0.8,
            "meanCompartmentalization": 0.75
        }
    }
    
    sample_file_metadata = [
        {"file_extension": "py", "path": "main.py"},
        {"file_extension": "js", "path": "app.js"}
    ]
    
    try:
        result = analyze_code_quality_with_chatgpt(sample_analysis_data, sample_file_metadata)
        print(f"   Analysis result keys: {list(result.keys())}")
        print(f"   Overall score: {result.get('overall_score', 'N/A')}")
        print(f"   AI percentage: {result.get('ai_percentage', 'N/A')}")
        print("   ✅ Sample analysis completed successfully")
    except Exception as e:
        print(f"   ❌ Sample analysis failed: {str(e)}")
    
    print()
    print("=== Debug script completed ===")

if __name__ == "__main__":
    main()
