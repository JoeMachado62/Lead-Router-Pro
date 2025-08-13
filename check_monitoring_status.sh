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
