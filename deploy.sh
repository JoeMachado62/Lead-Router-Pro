#!/bin/bash

# DockSide Pros Lead Router - Deployment Script
# This script sets up the lead router on a VPS

echo "🚀 DockSide Pros Lead Router - Deployment Script"
echo "================================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install Python 3 and pip
echo "🐍 Installing Python 3 and pip..."
apt install -y python3 python3-pip python3-venv

# Install nginx
echo "🌐 Installing Nginx..."
apt install -y nginx

# Install PM2 for process management
echo "⚙️ Installing PM2..."
apt install -y nodejs npm
npm install -g pm2

# Create application directory
APP_DIR="/opt/dockside-lead-router"
echo "📁 Creating application directory: $APP_DIR"
mkdir -p $APP_DIR
cd $APP_DIR

# Copy application files (assuming they're in current directory)
echo "📋 Copying application files..."
cp /path/to/your/files/* $APP_DIR/

# Create virtual environment
echo "🔧 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file from example
echo "⚙️ Setting up environment configuration..."
cp .env.example .env
echo "📝 Please edit /opt/dockside-lead-router/.env with your actual configuration"

# Create systemd service file
echo "🔧 Creating systemd service..."
cat > /etc/systemd/system/lead-router.service << EOF
[Unit]
Description=DockSide Pros Lead Router
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/gunicorn --bind 127.0.0.1:3000 --workers 2 webhook_server:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Create nginx configuration
echo "🌐 Setting up Nginx configuration..."
cat > /etc/nginx/sites-available/lead-router << EOF
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
EOF

# Enable nginx site
ln -sf /etc/nginx/sites-available/lead-router /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Set proper permissions
chown -R www-data:www-data $APP_DIR
chmod +x $APP_DIR/*.py

# Enable and start services
echo "🚀 Starting services..."
systemctl daemon-reload
systemctl enable lead-router
systemctl start lead-router
systemctl enable nginx
systemctl restart nginx

# Create log directory
mkdir -p /var/log/lead-router
chown www-data:www-data /var/log/lead-router

echo "✅ Deployment completed!"
echo ""
echo "📋 Next steps:"
echo "1. Edit $APP_DIR/.env with your GHL API credentials"
echo "2. Update the nginx server_name in /etc/nginx/sites-available/lead-router"
echo "3. Set up SSL certificate (recommended: certbot)"
echo "4. Test the webhook endpoint: http://your-domain.com/health"
echo ""
echo "🔧 Useful commands:"
echo "  systemctl status lead-router    # Check service status"
echo "  systemctl restart lead-router   # Restart service"
echo "  tail -f /var/log/lead-router/   # View logs"
echo "  nginx -t                        # Test nginx config"
echo ""
echo "🌐 Webhook URL: http://your-domain.com/webhook/elementor"
