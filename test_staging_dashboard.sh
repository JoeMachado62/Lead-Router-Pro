#!/bin/bash

echo "========================================"
echo "Testing Staging Dashboard Access"
echo "========================================"

# Check if dashboard file exists
if [ -f "staging/dynamic_forms/ui/dashboard.html" ]; then
    echo "✅ Dashboard HTML file found"
    echo "   Size: $(wc -c < staging/dynamic_forms/ui/dashboard.html) bytes"
else
    echo "❌ Dashboard HTML file not found"
    exit 1
fi

# Check Python dependencies
echo ""
echo "Checking Python environment..."
python3 -c "import fastapi; print('✅ FastAPI installed')" 2>/dev/null || echo "❌ FastAPI not installed - run: pip install fastapi"
python3 -c "import uvicorn; print('✅ Uvicorn installed')" 2>/dev/null || echo "❌ Uvicorn not installed - run: pip install uvicorn"
python3 -c "import sqlalchemy; print('✅ SQLAlchemy installed')" 2>/dev/null || echo "❌ SQLAlchemy not installed - run: pip install sqlalchemy"

echo ""
echo "========================================"
echo "To launch the staging dashboard:"
echo "========================================"
echo ""
echo "Option 1 - Simple launcher (recommended):"
echo "  python3 staging_dashboard_launcher.py"
echo ""
echo "Option 2 - Full staging system with sample data:"
echo "  python3 staging/test_staging_system.py"
echo ""
echo "Then open: http://localhost:8003/"
echo ""
echo "Note: Using port 8003 to avoid conflicts"
echo ""