#!/bin/bash

# Force update Seedance V2 to Gradio 5.42
echo "🔄 Forcing update to Gradio 5.42..."

# Stop all running services
systemctl stop seedance-v2 2>/dev/null || true
pkill -f "python.*app.py" 2>/dev/null || true
pkill -f "gradio" 2>/dev/null || true

# Change to working directory
cd /opt/seedance-v2

# Download latest files from GitHub (force refresh)
echo "📥 Downloading updated application files..."
curl -H "Cache-Control: no-cache" -o seedance-requirements.txt "https://raw.githubusercontent.com/kookliu/BP-Training-GenVideoWeb/main/ubuntu-seedance-v2/seedance-requirements.txt?$(date +%s)"
curl -H "Cache-Control: no-cache" -o app.py "https://raw.githubusercontent.com/kookliu/BP-Training-GenVideoWeb/main/ubuntu-seedance-v2/seedance-app.py?$(date +%s)"

# Verify files downloaded
echo "✅ Files updated:"
echo "- Requirements file size: $(wc -c < seedance-requirements.txt) bytes"
echo "- App file size: $(wc -c < app.py) bytes"

# Show Gradio version in requirements
echo "🔍 Checking Gradio version in requirements:"
grep gradio seedance-requirements.txt

# Update virtual environment with new requirements
echo "📦 Updating Python dependencies..."
source venv/bin/activate
pip install -r seedance-requirements.txt --upgrade

# Verify Gradio installation
echo "🔍 Checking installed Gradio version:"
pip show gradio | grep Version

# Start the application
echo "🚀 Starting Seedance V2 with Gradio 5.42..."
python app.py

echo "✅ Update complete! Application should be running on port 7860"