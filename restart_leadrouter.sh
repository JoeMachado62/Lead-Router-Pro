#!/bin/bash
# Lead Router Pro - Production Restart Script with Auto-Recovery
# Automatically stops service, checks dependencies, and restarts with monitoring

set -e  # Exit on error

echo "🔄 Lead Router Pro - Production Restart Script"
echo "============================================="
echo "Timestamp: $(date)"

# Configuration
APP_DIR="/root/Lead-Router-Pro"
SERVICE_NAME="leadrouter"
LOG_DIR="/var/log/leadrouter"
LOG_FILE="$LOG_DIR/restart.log"
PYTHON_EXEC="/root/Lead-Router-Pro/venv/bin/python"
UVICORN_EXEC="/root/Lead-Router-Pro/venv/bin/uvicorn"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to log messages
log_message() {
    echo "$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Function to check if service is running
is_service_running() {
    systemctl is-active --quiet "$SERVICE_NAME" && return 0 || return 1
}

# Stop the service if running
if is_service_running; then
    log_message "⏹️  Stopping $SERVICE_NAME service..."
    sudo systemctl stop "$SERVICE_NAME.service"
    sleep 3
else
    log_message "ℹ️  Service not running, proceeding with startup..."
fi

# Change to app directory
cd "$APP_DIR" || {
    log_message "❌ Failed to change to application directory: $APP_DIR"
    exit 1
}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    log_message "❌ Virtual environment not found!"
    log_message "🔧 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    log_message "✅ Virtual environment created and dependencies installed"
else
    source venv/bin/activate
fi

# Verify Python environment
log_message "🔍 Python environment check:"
log_message "   Python: $(which python)"
log_message "   Pip: $(which pip)"
log_message "   Uvicorn: $(which uvicorn || echo 'Not found - will install')"

# Install uvicorn if not present
if ! command -v uvicorn &> /dev/null; then
    log_message "📦 Installing uvicorn..."
    pip install uvicorn
fi

# Check for .env file
if [ ! -f ".env" ]; then
    log_message "⚠️  Warning: .env file not found. Application may not work correctly."
    log_message "   Please create .env file with required configuration."
fi

# Run dependency check
log_message ""
log_message "🛡️  CHECKING DEPENDENCIES..."
log_message "============================="

python -c "
import sys
sys.path.insert(0, '.')

try:
    from utils.dependency_manager import print_startup_report, can_start_application
    
    can_start = print_startup_report()
    
    if not can_start:
        print('❌ Critical dependencies missing. Cannot start application.')
        sys.exit(1)
    
    print('✅ All critical dependencies available.')
    
except ImportError as e:
    print('⚠️ Dependency manager not available, proceeding anyway...')
    print(f'   Error: {e}')
except Exception as e:
    print(f'⚠️ Error during dependency check: {e}')
    print('   Proceeding with startup...')
"

DEPENDENCY_CHECK=$?

if [ $DEPENDENCY_CHECK -ne 0 ]; then
    log_message "⚠️  Dependency check failed, but proceeding with startup..."
fi

# Update systemd service file if needed
log_message ""
log_message "🔧 Updating systemd service configuration..."

# Create updated service file
cat > /tmp/leadrouter.service << EOF
[Unit]
Description=Lead Router Pro FastAPI Application
After=network.target
StartLimitIntervalSec=300
StartLimitBurst=5

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONPATH=$APP_DIR"
EnvironmentFile=-$APP_DIR/.env
ExecStart=$PYTHON_EXEC -m uvicorn main_working_final:app --host 0.0.0.0 --port 8000 --workers 1 --log-level info
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=append:$LOG_DIR/app.log
StandardError=append:$LOG_DIR/error.log

# Restart configuration
RestartPreventExitStatus=0
SuccessExitStatus=0 143

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# Install the updated service file
sudo cp /tmp/leadrouter.service /etc/systemd/system/leadrouter.service
rm /tmp/leadrouter.service

# Reload systemd daemon
log_message "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable the service for auto-start on boot
sudo systemctl enable "$SERVICE_NAME.service" 2>/dev/null || true

# Start the service
log_message ""
log_message "🚀 Starting Lead Router Pro service..."
log_message "   - Server will be available at http://localhost:8000"
log_message "   - Admin dashboard: http://localhost:8000/dashboard"
log_message "   - API docs: http://localhost:8000/docs"
log_message "   - Health check: http://localhost:8000/health"
log_message ""

sudo systemctl start "$SERVICE_NAME.service"

# Wait for service to start
sleep 5

# Check if service started successfully
if is_service_running; then
    log_message "✅ Service started successfully!"
    log_message ""
    log_message "📊 Service Status:"
    systemctl status "$SERVICE_NAME.service" --no-pager | tee -a "$LOG_FILE"
    
    log_message ""
    log_message "📝 Useful commands:"
    log_message "   - View logs: journalctl -u $SERVICE_NAME -f"
    log_message "   - Check status: systemctl status $SERVICE_NAME"
    log_message "   - Stop service: systemctl stop $SERVICE_NAME"
    log_message "   - View app logs: tail -f $LOG_DIR/app.log"
    log_message "   - View error logs: tail -f $LOG_DIR/error.log"
    
    # Test health endpoint
    log_message ""
    log_message "🏥 Testing health endpoint..."
    sleep 2
    if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        log_message "✅ Health check passed!"
        curl -s http://localhost:8000/health | python -m json.tool || true
    else
        log_message "⚠️  Health check failed or server still starting..."
        log_message "   Check logs for details: journalctl -u $SERVICE_NAME -n 50"
    fi
else
    log_message "❌ Service failed to start!"
    log_message ""
    log_message "📋 Recent error logs:"
    journalctl -u "$SERVICE_NAME" --no-pager -n 30 | tee -a "$LOG_FILE"
    
    log_message ""
    log_message "🔍 Troubleshooting steps:"
    log_message "   1. Check logs: journalctl -u $SERVICE_NAME -f"
    log_message "   2. Check .env file exists and has correct values"
    log_message "   3. Verify Python dependencies: pip install -r requirements.txt"
    log_message "   4. Test manually: python main_working_final.py"
    log_message "   5. Check port 8000 is available: lsof -i :8000"
    
    exit 1
fi

log_message ""
log_message "🎉 Lead Router Pro is running in production mode with auto-restart enabled!"
log_message "   The service will automatically restart if it crashes."