#!/bin/bash
# Start backend server with proper environment

cd /Users/dhirennarne/Desktop/VibeCheck-Code-Reviewer-And-Grader
source venv/bin/activate
cd Backend

echo "Starting backend server..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
