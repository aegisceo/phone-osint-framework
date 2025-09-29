#!/bin/bash

# Security setup script for API keys
echo "Securing configuration files..."

# Set restrictive permissions on .env file
chmod 600 config/.env

# Create .gitignore if it doesn't exist
cat > .gitignore << 'EOF'
# Environment files
.env
config/.env
*.env

# API Keys
*api_key*
*api-key*
*apikey*

# Results and logs
results/
logs/
cache/
*.log

# Python
__pycache__/
*.py[cod]
venv/
.venv/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Sensitive data
*.pdf
*.csv
*.json
!config/*.json
EOF

echo "✓ Configuration secured"
echo ""
echo "⚠️  SECURITY REMINDERS:"
echo "1. NEVER commit .env to version control"
echo "2. Backup your API keys securely"
echo "3. Monitor API usage regularly"
echo "4. Rotate keys periodically"
echo ""
echo "Missing API Keys:"
echo "- Have I Been Pwned (required for breach checking)"
echo "- WhoisXML (optional)"