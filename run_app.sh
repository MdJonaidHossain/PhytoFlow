#!/bin/bash

# PhytoFlow Launch Script

echo "🌿 Starting PhytoFlow AI..."
echo ""

# Check if we're in the right directory
if [ ! -f "src/app.py" ]; then
    echo "❌ Error: Must run from PhytoFlow root directory"
    exit 1
fi

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Launch Streamlit app
echo "✅ Launching PhytoFlow..."
echo "📱 App will open in your browser at http://localhost:8501"
echo ""
streamlit run src/app.py
