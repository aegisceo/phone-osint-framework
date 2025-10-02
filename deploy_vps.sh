#!/bin/bash
#
# VPS Deployment Script for Phone OSINT Framework
# Deploys scraping service on a low-cost VPS
#
# Recommended VPS providers:
# - Hetzner Cloud: €4.50/month (2GB RAM, 40GB SSD)
# - DigitalOcean: $6/month (1GB RAM, 25GB SSD)
# - Vultr: $5/month (1GB RAM, 25GB SSD)
#

set -e  # Exit on error

echo "===================================="
echo "Phone OSINT VPS Deployment"
echo "===================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo ./deploy_vps.sh)"
    exit 1
fi

# Update system
echo "[1/8] Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq

# Install dependencies
echo "[2/8] Installing dependencies..."
apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    chromium-browser \
    chromium-chromedriver \
    nginx \
    supervisor

# Create app user
echo "[3/8] Creating application user..."
if ! id "phoneosint" &>/dev/null; then
    useradd -m -s /bin/bash phoneosint
fi

# Set up application directory
echo "[4/8] Setting up application directory..."
APP_DIR="/opt/phone-osint"
mkdir -p $APP_DIR
cd $APP_DIR

# Clone or copy repository (modify as needed)
echo "[5/8] Deploying application code..."
# Option 1: If deploying from this machine
# cp -r /path/to/phone-osint-framework/* $APP_DIR/

# Option 2: If deploying from git
# git clone https://github.com/yourusername/phone-osint-framework.git .

# For now, assume code is already here
chown -R phoneosint:phoneosint $APP_DIR

# Create virtual environment
echo "[6/8] Creating Python virtual environment..."
sudo -u phoneosint python3 -m venv $APP_DIR/venv

# Install Python dependencies
echo "[7/8] Installing Python packages..."
sudo -u phoneosint $APP_DIR/venv/bin/pip install --upgrade pip
sudo -u phoneosint $APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt

# Create config directory
mkdir -p $APP_DIR/config
mkdir -p $APP_DIR/results
chown -R phoneosint:phoneosint $APP_DIR/config
chown -R phoneosint:phoneosint $APP_DIR/results

# Set up environment file
if [ ! -f "$APP_DIR/config/.env" ]; then
    echo "[*] Creating .env template..."
    cp $APP_DIR/config/.env.example $APP_DIR/config/.env
    echo "IMPORTANT: Edit /opt/phone-osint/config/.env with your API keys!"
fi

# Configure supervisor for background processes
echo "[8/8] Configuring supervisor..."
cat > /etc/supervisor/conf.d/phone-osint.conf <<EOF
[program:phone-osint-web]
command=/opt/phone-osint/venv/bin/python /opt/phone-osint/web_interface.py
directory=/opt/phone-osint
user=phoneosint
autostart=true
autorestart=true
stderr_logfile=/var/log/phone-osint/web.err.log
stdout_logfile=/var/log/phone-osint/web.out.log
environment=PYTHONUNBUFFERED=1
EOF

# Create log directory
mkdir -p /var/log/phone-osint
chown phoneosint:phoneosint /var/log/phone-osint

# Configure nginx reverse proxy
echo "[*] Configuring nginx..."
cat > /etc/nginx/sites-available/phone-osint <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable nginx site
ln -sf /etc/nginx/sites-available/phone-osint /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx config
nginx -t

# Reload services
echo "[*] Starting services..."
supervisorctl reread
supervisorctl update
systemctl restart nginx

echo ""
echo "===================================="
echo "Deployment Complete!"
echo "===================================="
echo ""
echo "Next steps:"
echo "1. Edit /opt/phone-osint/config/.env with your API keys"
echo "2. Add proxies to /opt/phone-osint/config/proxies.txt (one per line, format: IP:PORT)"
echo "3. Start the web interface: supervisorctl start phone-osint-web"
echo "4. Access the web interface at: http://YOUR_VPS_IP"
echo ""
echo "Useful commands:"
echo "  - View logs: tail -f /var/log/phone-osint/web.out.log"
echo "  - Restart service: supervisorctl restart phone-osint-web"
echo "  - Check status: supervisorctl status"
echo ""
echo "To scrape free proxies:"
echo "  cd /opt/phone-osint && ./venv/bin/python scripts/proxy_scraper.py"
echo ""
