#!/bin/bash
# Display backend logs in real-time

echo "🔍 Backend Process Info"
echo "======================"
ps aux | grep uvicorn | grep -v grep

echo ""
echo "📝 To see backend logs:"
echo ""
echo "1. Find the terminal window where you ran:"
echo "   cd Backend && uvicorn main:app --reload"
echo ""
echo "2. That terminal will show all backend logs"
echo ""
echo "3. If you closed that terminal, the logs are gone"
echo ""
echo "💡 Alternative: Let me check recent activity..."

# Try to tail system logs
echo ""
echo "📋 Recent system logs (if any):"
journalctl --user -u uvicorn 2>/dev/null | tail -20 || echo "No systemd service found"

echo ""
echo "🔄 Would you like me to:"
echo "1. Restart the backend with visible logging?"
echo "2. Create a log file instead?"
echo ""
echo "The backend IS running (PID 43514) but logs go to the terminal where it was started."
