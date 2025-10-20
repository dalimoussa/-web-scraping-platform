#!/bin/bash
# Quick launcher for the Web UI Dashboard
# Run this file to start the web interface on macOS/Linux

echo "Starting Japanese Officials Data Collector Web UI..."
echo ""
echo "The web interface will open in your default browser."
echo "Press Ctrl+C to stop the server."
echo ""

cd "$(dirname "$0")"
source venv/bin/activate
streamlit run app.py
