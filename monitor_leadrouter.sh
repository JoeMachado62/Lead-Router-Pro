#!/bin/bash
# Lead Router Pro - Universal Health Monitor Script
# Checks if the service is running and healthy, supports both production and dev modes

# Configuration
SERVICE_NAME="leadrouter"
HEALTH_URL="http://localhost:8000/health"
LOG_DIR="/var/log/leadrouter"
MONITOR_LOG="$LOG_DIR/monitor.log"
MAX_RETRIES=3
RETRY_DELAY=10
MODE="${1:-production}"  # Default to production if not specified

# Create log directory if needed
mkdir -p "$LOG_DIR"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$MODE] $1" >> "$MONITOR_LOG"
}

# Function to check if dev mode is running
is_dev_mode_running() {
    # Check if any process is listening on port 8000
    if lsof -i :8000 | grep -q LISTEN; then
        # Check if it's a uvicorn process
        if ps aux | grep -v grep | grep -q "uvicorn.*main_working_final:app.*--reload"; then
            return 0
        fi
    fi
    return 1
}

# Function to restart based on mode
restart_service() {
    if [ "$MODE" = "dev" ]; then
        log_message "INFO: Development mode - cannot auto-restart (manual process)"
        log_message "INFO: To restart dev mode, run: ./restart_devmode_leadrouter.sh"
        return 1
    else
        log_message "INFO: Attempting to restart production service..."
        if systemctl restart "$SERVICE_NAME"; then
            log_message "SUCCESS: Service restarted successfully"
            return 0
        else
            log_message "ERROR: Failed to restart service"
            return 1
        fi
    fi
}

# Determine actual running mode if auto-detecting
if [ "$MODE" = "auto" ]; then
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        MODE="production"
        log_message "INFO: Auto-detected production mode (systemd service active)"
    elif is_dev_mode_running; then
        MODE="dev"
        log_message "INFO: Auto-detected development mode (uvicorn with --reload)"
    else
        log_message "WARNING: No running instance detected"
        MODE="production"  # Default to production for restart attempts
    fi
fi

# Check if service/process is active based on mode
service_active=false
if [ "$MODE" = "production" ]; then
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        service_active=true
    else
        log_message "WARNING: Production service $SERVICE_NAME is not active"
    fi
elif [ "$MODE" = "dev" ]; then
    if is_dev_mode_running; then
        service_active=true
    else
        log_message "WARNING: Development server is not running"
    fi
fi

# If not active, try to restart (production only)
if [ "$service_active" = false ] && [ "$MODE" = "production" ]; then
    if restart_service; then
        sleep 10  # Give service time to start
        service_active=true
    else
        exit 1
    fi
fi

# Check health endpoint
retry_count=0
health_check_passed=false

while [ $retry_count -lt $MAX_RETRIES ]; do
    if curl -s -f "$HEALTH_URL" > /dev/null 2>&1; then
        # Success - service is healthy
        health_check_passed=true
        break
    else
        retry_count=$((retry_count + 1))
        if [ $retry_count -lt $MAX_RETRIES ]; then
            log_message "WARNING: Health check failed (attempt $retry_count/$MAX_RETRIES). Waiting $RETRY_DELAY seconds..."
            sleep $RETRY_DELAY
        fi
    fi
done

# Handle health check results
if [ "$health_check_passed" = true ]; then
    # Only log on first check or after recovery
    if [ ! -f "$LOG_DIR/.last_health_status" ] || [ "$(cat $LOG_DIR/.last_health_status 2>/dev/null)" != "healthy" ]; then
        log_message "SUCCESS: Service is healthy ($MODE mode)"
        echo "healthy" > "$LOG_DIR/.last_health_status"
    fi
    exit 0
fi

# Health check failed after all retries
log_message "ERROR: Health check failed after $MAX_RETRIES attempts"

# Try to restart (production only)
if [ "$MODE" = "production" ]; then
    log_message "INFO: Attempting forced restart..."
    systemctl restart "$SERVICE_NAME"
    sleep 10
    
    # Final health check
    if curl -s -f "$HEALTH_URL" > /dev/null 2>&1; then
        log_message "SUCCESS: Service recovered after forced restart"
        echo "healthy" > "$LOG_DIR/.last_health_status"
    else
        log_message "CRITICAL: Service failed to recover after forced restart"
        echo "unhealthy" > "$LOG_DIR/.last_health_status"
        
        # Send alert (you can add email/webhook notification here)
        echo "Lead Router Pro service is down and could not be recovered!" | wall
        
        exit 1
    fi
else
    # Dev mode - just report the issue
    log_message "ERROR: Development server health check failed. Manual intervention required."
    log_message "INFO: To restart dev mode, run: ./restart_devmode_leadrouter.sh"
    echo "unhealthy" > "$LOG_DIR/.last_health_status"
    exit 1
fi