#!/bin/bash
# Lead Router Pro - Quick Restart Script (Dev Mode)
# Automatically stops service, reloads configs, and restarts in dev mode

echo "🔄 Lead Router Pro - Restart Script (Dev Mode)"
echo "=================================="

# Stop the service
echo "⏹️  Stopping any process on port 8000..."
fuser -k -n tcp 8000

# Wait a moment for clean shutdown
echo "⏳ Waiting for clean shutdown..."
sleep 5

# Change to app directory
echo "📁 Changing to Lead-Router-Pro directory..."
cd /root/Lead-Router-Pro

# Activate virtual environment and start
echo "🐍 Activating virtual environment..."
source venv/bin/activate

echo "🚀 Starting Lead Router Pro in Dev Mode..."
echo "   - Server will be available at http://localhost:8000"
echo "   - Press Ctrl+C to stop"
echo "   - Logs will appear below..."
echo ""

# Start the application in dev mode
python -m uvicorn main_working_final:app --host 0.0.0.0 --port 8000 --log-level trace
