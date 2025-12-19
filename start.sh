#!/bin/bash

# Launch script for Car Manual Q&A System

echo "🚗 Car Manual Q&A System"
echo "=========================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "ℹ️  No .env file found. The app will work without API key."
    echo "   For better answers, add OPENAI_API_KEY to .env file"
    echo "   See GET_API_KEY.md for instructions"
    echo ""
fi

# Check PDFs
if [ ! -f "Astor Manual.pdf" ] || [ ! -f "APP-TIAGO-FINAL-OMSB.pdf" ]; then
    echo "⚠️  Warning: PDF files not found in current directory"
    echo ""
fi

echo "Starting Streamlit app..."
echo "Press Ctrl+C to stop"
echo ""

# Launch streamlit
python3 -m streamlit run app.py
