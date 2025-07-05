#!/bin/bash
# Lead Router Pro - Quick Restart Script (Dev Mode) with Dependency Management
# Automatically stops service, checks dependencies, and restarts in dev mode

echo "🔄 Lead Router Pro - Restart Script (Dev Mode)"
echo "=================================="

# Stop the service
echo "⏹️  Stopping any process on port 8000..."
fuser -k -n tcp 8000 2>/dev/null || echo "   No process found on port 8000"

# Wait a moment for clean shutdown
echo "⏳ Waiting for clean shutdown..."
sleep 5

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
        print('🔧 AUTO-INSTALLATION SCRIPT:')
        print('=============================')
        script = dependency_manager.get_installation_script()
        print(script)
        print('')
        
        # Ask user if they want to auto-install missing critical dependencies
        import subprocess
        response = input('❓ Would you like to auto-install missing critical dependencies? (y/n): ').strip().lower()
        
        if response in ['y', 'yes']:
            print('📦 Installing missing dependencies...')
            
            # Get missing critical dependencies
            missing_critical = dependency_manager._get_missing_critical()
            for dep_name in missing_critical:
                dep_info = next(d for d in dependency_manager.dependency_map.values() if d.name == dep_name)
                print(f'Installing {dep_name}...')
                try:
                    result = subprocess.run(dep_info.install_command.split(), check=True, capture_output=True, text=True)
                    print(f'✅ {dep_name} installed successfully')
                except subprocess.CalledProcessError as e:
                    print(f'❌ Failed to install {dep_name}: {e}')
            
            # Re-check dependencies after installation
            print('')
            print('🔄 RE-CHECKING DEPENDENCIES AFTER INSTALLATION...')
            print('=============================================')
            
            # Reload the dependency manager
            from importlib import reload
            import utils.dependency_manager
            reload(utils.dependency_manager)
            from utils.dependency_manager import print_startup_report, can_start_application
            
            can_start = print_startup_report()
            
            if not can_start:
                print('❌ Still missing critical dependencies. Cannot start application.')
                sys.exit(1)
        else:
            print('❌ User chose not to install dependencies. Cannot start application.')
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
    echo "   Please resolve dependency issues and try again."
    exit 1
fi

echo ""
echo "🚀 Starting Lead Router Pro in Dev Mode..."
echo "   - Server will be available at http://localhost:8000"
echo "   - Health check: http://localhost:8000/health"
echo "   - API docs: http://localhost:8000/docs"
echo "   - Press Ctrl+C to stop"
echo "   - Logs will appear below..."
echo ""

# Start the application in dev mode with reload
echo "🔥 Starting with auto-reload (development mode)..."
python -m uvicorn main_working_final:app --host 0.0.0.0 --port 8000 --log-level trace --reload