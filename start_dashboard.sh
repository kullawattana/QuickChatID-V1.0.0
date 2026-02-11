#!/bin/bash

# QuickChat ID Dashboard Startup Script

echo "=========================================="
echo "QuickChat ID - KYC Dashboard"
echo "=========================================="
echo ""

# Check if SQLAlchemy is installed
if ! python -c "import sqlalchemy" 2>/dev/null; then
    echo "Installing SQLAlchemy..."
    pip install sqlalchemy
fi

echo "✓ Dependencies installed"
echo ""

# Initialize database
echo "Initializing database..."
python -c "from database import init_db; init_db()"

echo ""
echo "=========================================="
echo "Starting Dashboard Server..."
echo "=========================================="
echo ""

# Start the dashboard server
python dashboard_app.py
