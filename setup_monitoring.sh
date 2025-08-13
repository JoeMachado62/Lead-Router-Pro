#!/bin/bash
# Setup monitoring for Lead Router Pro (supports both production and dev modes)

echo "🔧 Setting up Lead Router Pro monitoring..."
echo "=========================================="

# Ask user about monitoring mode
echo ""
echo "Select monitoring mode:"
echo "1) Production mode (systemd service)"
echo "2) Development mode (uvicorn with --reload)"
echo "3) Auto-detect mode (recommended)"
echo ""
read -p "Enter choice [1-3] (default: 3): " MODE_CHOICE

case $MODE_CHOICE in
    1)
        MONITOR_MODE="production"
        ;;
    2)
        MONITOR_MODE="dev"
        ;;
    *)
        MONITOR_MODE="auto"
        ;;
esac

echo "✅ Selected monitoring mode: $MONITOR_MODE"

# Add cron job for monitoring
if [ "$MONITOR_MODE" = "dev" ]; then
    # Less frequent checks for dev mode to avoid log spam
    CRON_SCHEDULE="*/10 * * * *"  # Every 10 minutes
    CRON_DESC="every 10 minutes"
else
    # More frequent checks for production
    CRON_SCHEDULE="*/5 * * * *"   # Every 5 minutes
    CRON_DESC="every 5 minutes"
fi

CRON_JOB="$CRON_SCHEDULE /root/Lead-Router-Pro/monitor_leadrouter.sh $MONITOR_MODE > /dev/null 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "monitor_leadrouter.sh"; then
    echo "⚠️  Removing existing monitoring cron job..."
    # Remove existing job
    crontab -l 2>/dev/null | grep -v "monitor_leadrouter.sh" | crontab -
fi

# Add the new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
echo "✅ Added monitoring cron job (runs $CRON_DESC in $MONITOR_MODE mode)"

# Create log rotation config
cat > /etc/logrotate.d/leadrouter << EOF
/var/log/leadrouter/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
    sharedscripts
    postrotate
        # Only reload if production service is active
        if systemctl is-active --quiet leadrouter; then
            systemctl reload leadrouter > /dev/null 2>&1 || true
        fi
    endscript
}
EOF

echo "✅ Configured log rotation"

# Create monitoring status script
cat > /root/Lead-Router-Pro/check_monitoring_status.sh << 'EOF'
#!/bin/bash
echo "📊 Lead Router Pro Monitoring Status"
echo "===================================="
echo ""

# Check cron job
echo "🕐 Scheduled Monitoring:"
if crontab -l 2>/dev/null | grep -q "monitor_leadrouter.sh"; then
    echo "✅ Monitoring cron job is active"
    crontab -l | grep "monitor_leadrouter.sh" | sed 's/^/   /'
else
    echo "❌ No monitoring cron job found"
fi

echo ""
echo "📋 Recent Monitor Logs:"
if [ -f /var/log/leadrouter/monitor.log ]; then
    tail -n 10 /var/log/leadrouter/monitor.log | sed 's/^/   /'
else
    echo "   No monitor logs found"
fi

echo ""
echo "🏥 Current Health Status:"
if [ -f /var/log/leadrouter/.last_health_status ]; then
    status=$(cat /var/log/leadrouter/.last_health_status)
    if [ "$status" = "healthy" ]; then
        echo "✅ Service is healthy"
    else
        echo "❌ Service is unhealthy"
    fi
else
    echo "❓ Health status unknown"
fi

echo ""
echo "📊 Service Status:"
# Check production service
if systemctl is-active --quiet leadrouter; then
    echo "✅ Production service is running"
    systemctl status leadrouter --no-pager --lines=3 | grep -E "(Active|Main PID)" | sed 's/^/   /'
else
    echo "ℹ️  Production service is not active"
fi

# Check dev mode
if ps aux | grep -v grep | grep -q "uvicorn.*main_working_final:app.*--reload"; then
    echo "✅ Development server is running"
    ps aux | grep -v grep | grep "uvicorn.*main_working_final:app.*--reload" | awk '{print "   PID:", $2, "Started:", $9}' | head -1
else
    echo "ℹ️  Development server is not running"
fi

echo ""
echo "📁 Log Files:"
echo "   Monitor log: /var/log/leadrouter/monitor.log"
echo "   App log: /var/log/leadrouter/app.log"
echo "   Error log: /var/log/leadrouter/error.log"
echo "   Dev mode log: /var/log/leadrouter/devmode.log"
EOF

chmod +x /root/Lead-Router-Pro/check_monitoring_status.sh

# Test the monitor script
echo ""
echo "🧪 Testing monitor script..."
/root/Lead-Router-Pro/monitor_leadrouter.sh $MONITOR_MODE
if [ $? -eq 0 ]; then
    echo "✅ Monitor script test passed"
else
    echo "⚠️  Monitor script detected issues - check logs"
fi

echo ""
echo "📊 Monitoring setup complete!"
echo "===================================="
echo ""
echo "Mode: $MONITOR_MODE"
echo "Schedule: Health checks run $CRON_DESC"
echo "Logs: Rotate daily (kept for 14 days)"
echo ""
echo "Useful commands:"
echo "  - Check monitoring status: ./check_monitoring_status.sh"
echo "  - View monitor logs: tail -f /var/log/leadrouter/monitor.log"
echo "  - View cron schedule: crontab -l"
echo "  - Manual health check: ./monitor_leadrouter.sh $MONITOR_MODE"
echo "  - Disable monitoring: crontab -l | grep -v monitor_leadrouter.sh | crontab -"
echo ""

if [ "$MONITOR_MODE" = "auto" ]; then
    echo "ℹ️  Auto-detect mode will automatically determine if you're running"
    echo "   production (systemd) or development (uvicorn --reload) mode."
fi