#!/bin/bash
# Lead Router Pro - Quick Restart Script
# Automatically stops service, reloads configs, and restarts

echo "🔄 Lead Router Pro - Restart Script"
echo "=================================="

# Stop the service
echo "⏹️  Stopping leadrouter service..."
sudo systemctl stop leadrouter.service

# Reload systemd daemon
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

# Wait a moment for clean shutdown
echo "⏳ Waiting for clean shutdown..."
sleep 3

# Change to app directory
echo "📁 Changing to Lead-Router-Pro directory..."
cd /root/Lead-Router-Pro

# Activate virtual environment and start
echo "🐍 Activating virtual environment..."
source venv/bin/activate

echo "🚀 Starting Lead Router Pro..."
echo "   - Server will be available at http://localhost:8000"
echo "   - Press Ctrl+C to stop"
echo "   - Logs will appear below..."
echo ""

# Start the application
python main_working_final.py