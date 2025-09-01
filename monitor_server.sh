#!/bin/bash

# Lead Router Pro - Live Traffic Monitor
# This script monitors the running server's output in real-time

echo "🔍 Lead Router Pro - Live Traffic Monitor"
echo "=========================================="
echo ""

# Check if server is running
if lsof -i :8000 | grep -q LISTEN; then
    echo "✅ Server is running on port 8000"
    echo ""
    
    # Option 1: Monitor the log file
    if [ -f /var/log/leadrouter/devmode.log ]; then
        echo "📋 Monitoring log file: /var/log/leadrouter/devmode.log"
        echo "   Press Ctrl+C to stop monitoring"
        echo ""
        echo "----------------------------------------"
        tail -f /var/log/leadrouter/devmode.log
    else
        echo "⚠️  Log file not found at /var/log/leadrouter/devmode.log"
        echo ""
        echo "Alternative: Start server in foreground mode:"
        echo "  python -m uvicorn main_working_final:app --host 0.0.0.0 --port 8000 --log-level debug --reload"
    fi
else
    echo "❌ Server is not running on port 8000"
    echo ""
    echo "Start the server with:"
    echo "  ./restart_devmode_leadrouter.sh"
    echo ""
    echo "Or run in foreground for live output:"
    echo "  python -m uvicorn main_working_final:app --host 0.0.0.0 --port 8000 --log-level debug --reload"
fi