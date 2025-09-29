#!/bin/bash

# Phone OSINT Investigation Runner
# Usage: ./run_investigation.sh +1234567890

PHONE_NUMBER=$1

if [ -z "$PHONE_NUMBER" ]; then
    echo "Usage: $0 <phone_number>"
    echo "Example: $0 +1234567890"
    exit 1
fi

echo "====================================="
echo "Phone OSINT Investigation Framework"
echo "====================================="
echo "Target: $PHONE_NUMBER"
echo "Time: $(date)"
echo "====================================="

# Activate virtual environment
source venv/bin/activate

# Ensure Redis is running
sudo service redis-server start

# Run the investigation
python phone_osint_master.py "$PHONE_NUMBER"

# Check if report was generated
LATEST_RESULT=$(ls -t results/*/investigation_report.html | head -1)

if [ -f "$LATEST_RESULT" ]; then
    echo ""
    echo "Opening report in browser..."
    xdg-open "$LATEST_RESULT" 2>/dev/null || open "$LATEST_RESULT" 2>/dev/null
else
    echo "Error: Report generation failed"
fi