#!/bin/bash
# Lead Router Pro - Quick Restart Script (Production) with Dependency Management
# Automatically stops service, checks dependencies, and restarts

echo "🔄 Lead Router Pro - Restart Script (Production)"
echo "============================================="

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

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Check Python path
echo "🔍 Using Python: $(which python)"
echo "🔍 Using pip: $(which pip)"

# Run dependency check and startup report
echo ""
echo "🛡️ CHECKING DEPENDENCIES..."
echo "============================="

# Run the dependency management system
python -c "
import sys
sys.path.insert(0, '.')

try:
    from utils.dependency_manager import print_startup_report, can_start_application, dependency_manager
    
    # Print comprehensive startup report
    can_start = print_startup_report()
    
    if not can_start:
        print('')
        print('💥 CANNOT START APPLICATION')
        print('===========================')
        print('Critical dependencies are missing. Application cannot start.')
        print('')
        print('🔧 REQUIRED INSTALLATIONS:')
        print('==========================')
        
        # Get missing critical dependencies
        missing_critical = dependency_manager._get_missing_critical()
        for dep_name in missing_critical:
            dep_info = next(d for d in dependency_manager.dependency_map.values() if d.name == dep_name)
            print(f'❌ {dep_name}: {dep_info.install_command}')
        
        print('')
        print('📝 Run the following commands to install missing dependencies:')
        for dep_name in missing_critical:
            dep_info = next(d for d in dependency_manager.dependency_map.values() if d.name == dep_name)
            print(f'   {dep_info.install_command}')
        
        print('')
        print('Or save this auto-install script:')
        script = dependency_manager.get_installation_script()
        with open('install_missing_deps.sh', 'w') as f:
            f.write(script)
        print('   Script saved as: install_missing_deps.sh')
        print('   Run with: chmod +x install_missing_deps.sh && ./install_missing_deps.sh')
        
        sys.exit(1)
    
    print('✅ All critical dependencies available. Ready to start application!')
    
except ImportError as e:
    print('⚠️ Dependency management system not available.')
    print(f'   Error: {e}')
    print('   Proceeding with basic startup (may encounter issues)...')
except Exception as e:
    print(f'⚠️ Error during dependency check: {e}')
    print('   Proceeding with basic startup...')
"

# Check if dependency check passed
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Dependency check failed. Cannot start application."
    echo "   Please install missing dependencies and try again."
    echo ""
    echo "🔧 Quick fix options:"
    echo "   1. Run: ./install_missing_deps.sh (if generated)"
    echo "   2. Install manually using the commands shown above"
    echo "   3. Run: pip install -r requirements.txt"
    exit 1
fi

# Check if we should start as systemd service or directly
if systemctl is-enabled leadrouter.service >/dev/null 2>&1; then
    echo ""
    echo "🚀 Starting Lead Router Pro via systemd service..."
    echo "   - Server will be available at http://localhost:8000"
    echo "   - Check status: systemctl status leadrouter"
    echo "   - View logs: journalctl -u leadrouter -f"
    echo ""
    
    sudo systemctl start leadrouter.service
    sleep 2
    
    # Check if service started successfully
    if systemctl is-active --quiet leadrouter.service; then
        echo "✅ Service started successfully!"
        systemctl status leadrouter.service --no-pager
    else
        echo "❌ Service failed to start!"
        echo "📋 Service logs:"
        journalctl -u leadrouter --no-pager -n 20
        exit 1
    fi
else
    echo ""
    echo "🚀 Starting Lead Router Pro directly (systemd service not configured)..."
    echo "   - Server will be available at http://localhost:8000"
    echo "   - Health check: http://localhost:8000/health"
    echo "   - API docs: http://localhost:8000/docs"
    echo "   - Press Ctrl+C to stop"
    echo "   - Logs will appear below..."
    echo ""
    
    # Start the application directly
    python main_working_final.py
fi