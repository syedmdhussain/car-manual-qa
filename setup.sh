#!/bin/bash

# Setup script for Car Manual Q&A System

echo "🚗 Car Manual Q&A System - Setup"
echo "=================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the application, use:"
echo "  streamlit run app.py"
echo ""
