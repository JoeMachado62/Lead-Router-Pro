# Lead Router Pro - VPS Deployment Plan
## Server: dockside.life (167.88.39.177)

### Phase 1: Initial Server Setup & Security

#### 1.1 System Updates & Basic Security
```bash
# Update system packages
apt update && apt upgrade -y

# Install essential packages
apt install -y curl wget git htop nano ufw fail2ban

# Configure firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp  # For initial testing
ufw --force enable

# Configure fail2ban for SSH protection
systemctl enable fail2ban
systemctl start fail2ban
```

#### 1.2 Create Application User
```bash
# Create dedicated user for the application
adduser leadrouter
usermod -aG sudo leadrouter

# Set up SSH key access for leadrouter user
mkdir -p /home/leadrouter/.ssh
cp /root/.ssh/authorized_keys /home/leadrouter/.ssh/
chown -R leadrouter:leadrouter /home/leadrouter/.ssh
chmod 700 /home/leadrouter/.ssh
chmod 600 /home/leadrouter/.ssh/authorized_keys
```

### Phase 2: Environment Setup

#### 2.1 Install Python & Dependencies
```bash
# Install Python 3.11+ and pip
apt install -y python3 python3-pip python3-venv python3-dev

# Install system dependencies for Python packages
apt install -y build-essential libssl-dev libffi-dev python3-setuptools

# Install Node.js (if needed for any frontend tools)
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs
```

#### 2.2 Install Database (SQLite + backup strategy)
```bash
# Install SQLite (already included in Ubuntu)
apt install -y sqlite3

# Create database directory
mkdir -p /var/lib/leadrouter/db
chown leadrouter:leadrouter /var/lib/leadrouter/db
```

#### 2.3 Install Web Server Components
```bash
# Install Nginx
apt install -y nginx

# Install Redis (for caching/sessions if needed)
apt install -y redis-server
systemctl enable redis-server
systemctl start redis-server
```

### Phase 3: Application Deployment

#### 3.1 Clone Repository
```bash
# Switch to leadrouter user
su - leadrouter

# Clone the repository
cd /home/leadrouter
git clone https://github.com/JoeMachado62/Lead-Router-Pro.git
cd Lead-Router-Pro

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3.2 Environment Configuration
```bash
# Copy and configure environment file
cp .env.example .env
nano .env

# Configure the following variables:
# GHL_LOCATION_ID=your_location_id
# GHL_API_KEY=your_api_key
# GHL_PRIVATE_TOKEN=your_private_token
# GHL_AGENCY_API_KEY=your_agency_api_key
# DATABASE_URL=sqlite:///var/lib/leadrouter/db/smart_lead_router.db
# ENVIRONMENT=production
# DEBUG=False
# ALLOWED_HOSTS=dockside.life,167.88.39.177
```

#### 3.3 Database Setup
```bash
# Create database directory and set permissions
sudo mkdir -p /var/lib/leadrouter/db
sudo chown leadrouter:leadrouter /var/lib/leadrouter/db

# Initialize database (if you have migration scripts)
python database/simple_connection.py  # Or your init script
```

### Phase 4: Web Server Configuration

#### 4.1 Configure Gunicorn/Uvicorn Service
```bash
# Create systemd service file
sudo nano /etc/systemd/system/leadrouter.service
```

**Service file content:**
```ini
[Unit]
Description=Lead Router Pro FastAPI application
After=network.target

[Service]
Type=notify
User=leadrouter
Group=leadrouter
RuntimeDirectory=leadrouter
WorkingDirectory=/home/leadrouter/Lead-Router-Pro
Environment=PATH=/home/leadrouter/Lead-Router-Pro/venv/bin
ExecStart=/home/leadrouter/Lead-Router-Pro/venv/bin/uvicorn main_working_final:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

#### 4.2 Configure Nginx Reverse Proxy
```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/dockside.life
```

**Nginx configuration:**
```nginx
server {
    listen 80;
    server_name dockside.life www.dockside.life 167.88.39.177;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Webhook endpoints - higher rate limits
    location /api/v1/webhooks/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Increase limits for webhooks
        client_max_body_size 10M;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }

    # Static files (if any)
    location /static/ {
        alias /home/leadrouter/Lead-Router-Pro/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 4.3 Enable Nginx Configuration
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/dockside.life /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Phase 5: SSL Certificate Setup

#### 5.1 Install Certbot and Get SSL Certificate
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d dockside.life -d www.dockside.life

# Test automatic renewal
sudo certbot renew --dry-run
```

### Phase 6: Start Services

#### 6.1 Enable and Start Application Services
```bash
# Enable and start Lead Router service
sudo systemctl daemon-reload
sudo systemctl enable leadrouter
sudo systemctl start leadrouter

# Check status
sudo systemctl status leadrouter

# View logs
sudo journalctl -u leadrouter -f
```

### Phase 7: Domain Configuration

#### 7.1 DNS Configuration (if managing DNS)
```
A Record: dockside.life → 167.88.39.177
A Record: www.dockside.life → 167.88.39.177
```

### Phase 8: Monitoring & Logging

#### 8.1 Set up Log Rotation
```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/leadrouter
```

**Logrotate config:**
```
/var/log/leadrouter/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    create 644 leadrouter leadrouter
    postrotate
        systemctl reload leadrouter
    endscript
}
```

#### 8.2 Basic Monitoring Script
```bash
# Create monitoring script
nano /home/leadrouter/monitor.sh
```

**Monitor script:**
```bash
#!/bin/bash
# Basic health monitoring for Lead Router Pro

LOG_FILE="/var/log/leadrouter/monitor.log"
API_URL="http://localhost:8000/api/v1/webhooks/health"

# Check if service is running
if ! systemctl is-active --quiet leadrouter; then
    echo "$(date): Lead Router service is down!" >> $LOG_FILE
    systemctl restart leadrouter
fi

# Check API health
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $API_URL)
if [ "$HTTP_STATUS" != "200" ]; then
    echo "$(date): API health check failed with status $HTTP_STATUS" >> $LOG_FILE
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "$(date): Disk usage is at ${DISK_USAGE}%" >> $LOG_FILE
fi
```

```bash
# Make executable and add to cron
chmod +x /home/leadrouter/monitor.sh
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/leadrouter/monitor.sh") | crontab -
```

### Phase 9: Backup Strategy

#### 9.1 Database Backup Script
```bash
# Create backup script
nano /home/leadrouter/backup.sh
```

**Backup script:**
```bash
#!/bin/bash
BACKUP_DIR="/home/leadrouter/backups"
DB_PATH="/var/lib/leadrouter/db/smart_lead_router.db"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database backup
cp $DB_PATH "$BACKUP_DIR/db_backup_$DATE.db"

# Application backup
tar -czf "$BACKUP_DIR/app_backup_$DATE.tar.gz" -C /home/leadrouter Lead-Router-Pro

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

```bash
# Make executable and schedule
chmod +x /home/leadrouter/backup.sh
(crontab -l 2>/dev/null; echo "0 2 * * * /home/leadrouter/backup.sh") | crontab -
```

### Phase 10: Testing & Validation

#### 10.1 Application Testing
```bash
# Test health endpoint
curl http://dockside.life/api/v1/webhooks/health

# Test webhook endpoint (with sample payload)
curl -X POST http://dockside.life/api/v1/webhooks/ghl/vendor-user-creation \
  -H "Content-Type: application/json" \
  -d '{"contact_id": "test", "event_type": "vendor_approved"}'
```

#### 10.2 Performance Testing
```bash
# Install testing tools
sudo apt install -y apache2-utils

# Basic load test
ab -n 100 -c 10 http://dockside.life/api/v1/webhooks/health
```

### Phase 11: Security Hardening

#### 11.1 Additional Security Measures
```bash
# Install additional security tools
sudo apt install -y rkhunter chkrootkit

# Configure automatic security updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# Set up file integrity monitoring
sudo apt install -y aide
sudo aideinit
sudo cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db
```

### Phase 12: Production Checklist

- [ ] Server secured and hardened
- [ ] Application deployed and running
- [ ] SSL certificate installed and auto-renewal configured
- [ ] Firewall properly configured
- [ ] Monitoring and logging in place
- [ ] Backup strategy implemented
- [ ] DNS pointing to server
- [ ] Health checks passing
- [ ] Webhook endpoints tested
- [ ] Performance benchmarks established
- [ ] Error alerting configured
- [ ] Documentation updated

### Environment Variables for Production

```bash
# Required environment variables in /home/leadrouter/Lead-Router-Pro/.env
ENVIRONMENT=production
DEBUG=False
ALLOWED_HOSTS=dockside.life,www.dockside.life,167.88.39.177
DATABASE_URL=sqlite:///var/lib/leadrouter/db/smart_lead_router.db

# GHL Configuration
GHL_LOCATION_ID=your_location_id
GHL_API_KEY=your_api_key
GHL_PRIVATE_TOKEN=your_private_token
GHL_AGENCY_API_KEY=your_agency_api_key

# Security
SECRET_KEY=generate_random_secret_key_here
CORS_ORIGINS=https://dockside.life,https://www.dockside.life

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/leadrouter/app.log
```

### Next Steps After Deployment

1. **Update GoHighLevel Webhook URLs**: Change from local URLs to https://dockside.life/api/v1/webhooks/...
2. **Test All Webhook Endpoints**: Verify each form type works correctly
3. **Monitor Initial Traffic**: Watch logs for any issues
4. **Performance Optimization**: Adjust worker counts based on load
5. **Set Up Alerts**: Configure email/SMS notifications for critical issues
6. **Regular Maintenance**: Schedule weekly health checks and updates

This plan provides a complete production-ready deployment with security, monitoring, and backup strategies in place.
