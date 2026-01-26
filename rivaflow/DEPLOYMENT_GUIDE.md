# RivaFlow Deployment Guide - Hostinger VPS

## Prerequisites

- Hostinger VPS with 4GB RAM, 2 vCPUs, SSD storage
- Domain or subdomain pointed to VPS IP
- SSH access to VPS
- Ubuntu 20.04+ or Debian-based Linux

## Overview

This guide deploys:
- FastAPI backend on port 8000
- React frontend (production build) on port 3000
- Ollama with llama3.2:3b model
- Nginx as reverse proxy with SSL
- Systemd services for auto-restart

---

## Phase 1: Server Access & Initial Setup

### 1.1 SSH into VPS

```bash
ssh root@YOUR_VPS_IP
# Or: ssh username@YOUR_VPS_IP
```

### 1.2 Update System

```bash
apt update && apt upgrade -y
```

### 1.3 Install Basic Dependencies

```bash
apt install -y git curl wget build-essential ufw nginx python3 python3-pip python3-venv nodejs npm
```

### 1.4 Verify Installations

```bash
python3 --version  # Should be 3.8+
node --version     # Should be 14+
npm --version
nginx -v
```

---

## Phase 2: Install Ollama

### 2.1 Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 2.2 Start Ollama Service

```bash
systemctl start ollama
systemctl enable ollama
systemctl status ollama
```

### 2.3 Pull Model (This will take 5-10 minutes)

```bash
ollama pull llama3.2:3b
# Model is ~2GB, will download and cache
```

### 2.4 Test Ollama

```bash
curl http://localhost:11434/api/tags
# Should show llama3.2:3b in the list
```

---

## Phase 3: Deploy Application

### 3.1 Create App Directory

```bash
mkdir -p /var/www/rivaflow
cd /var/www/rivaflow
```

### 3.2 Clone Repository

```bash
git clone https://github.com/RubyWolff27/rivaflow.git .
# Or if private: git clone git@github.com:RubyWolff27/rivaflow.git .
```

### 3.3 Set Up Backend

```bash
cd /var/www/rivaflow/rivaflow

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create database directory
mkdir -p ~/.rivaflow

# Test backend
uvicorn rivaflow.api.main:app --host 0.0.0.0 --port 8000
# Press Ctrl+C after confirming it starts
```

### 3.4 Set Up Frontend

```bash
cd /var/www/rivaflow/web

# Install dependencies
npm install

# Build production bundle
npm run build
# Creates /var/www/rivaflow/web/dist folder
```

---

## Phase 4: Configure Environment Variables

### 4.1 Create Backend .env File

```bash
cat > /var/www/rivaflow/rivaflow/.env << 'EOF'
# JWT Secret (generate a random string)
SECRET_KEY=YOUR_RANDOM_SECRET_KEY_HERE_CHANGE_THIS
DATABASE_PATH=/root/.rivaflow/rivaflow.db

# Production settings
ENVIRONMENT=production
ALLOWED_ORIGINS=https://rivaflow.yourdomain.com
EOF
```

**Generate a secure secret key:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy output and replace SECRET_KEY above
```

### 4.2 Update Frontend API URL

Edit `/var/www/rivaflow/web/src/config.ts` (or wherever API URL is configured):

```bash
# If you have a config file, update API_BASE_URL to:
# https://rivaflow.yourdomain.com/api
```

**Then rebuild frontend:**
```bash
cd /var/www/rivaflow/web
npm run build
```

---

## Phase 5: Set Up Systemd Services

### 5.1 Create Backend Service

```bash
cat > /etc/systemd/system/rivaflow-api.service << 'EOF'
[Unit]
Description=RivaFlow FastAPI Backend
After=network.target ollama.service
Requires=ollama.service

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/rivaflow/rivaflow
Environment="PATH=/var/www/rivaflow/rivaflow/venv/bin"
ExecStart=/var/www/rivaflow/rivaflow/venv/bin/uvicorn rivaflow.api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 5.2 Create Frontend Service (Static File Server)

```bash
# Install serve globally for static hosting
npm install -g serve

cat > /etc/systemd/system/rivaflow-web.service << 'EOF'
[Unit]
Description=RivaFlow React Frontend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/rivaflow/web
ExecStart=/usr/bin/npx serve -s dist -l 3000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 5.3 Enable and Start Services

```bash
systemctl daemon-reload
systemctl enable rivaflow-api rivaflow-web
systemctl start rivaflow-api rivaflow-web

# Check status
systemctl status rivaflow-api
systemctl status rivaflow-web
```

---

## Phase 6: Configure Nginx Reverse Proxy

### 6.1 Create Nginx Config

```bash
cat > /etc/nginx/sites-available/rivaflow << 'EOF'
server {
    listen 80;
    server_name rivaflow.yourdomain.com;  # CHANGE THIS

    # Redirect HTTP to HTTPS (after SSL is set up)
    # return 301 https://$server_name$request_uri;

    # API Backend
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 60s;
    }

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF
```

### 6.2 Enable Site

```bash
ln -s /etc/nginx/sites-available/rivaflow /etc/nginx/sites-enabled/
nginx -t  # Test configuration
systemctl reload nginx
```

---

## Phase 7: Configure SSL with Let's Encrypt

### 7.1 Install Certbot

```bash
apt install -y certbot python3-certbot-nginx
```

### 7.2 Obtain SSL Certificate

```bash
certbot --nginx -d rivaflow.yourdomain.com
# Follow prompts, agree to terms
# Choose option 2: Redirect HTTP to HTTPS
```

### 7.3 Test Auto-Renewal

```bash
certbot renew --dry-run
```

---

## Phase 8: Configure Firewall

```bash
# Allow SSH, HTTP, HTTPS
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp

# Enable firewall
ufw enable
ufw status
```

---

## Phase 9: Update CORS Settings

Edit `/var/www/rivaflow/rivaflow/api/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:3000",
        "https://rivaflow.yourdomain.com",  # ADD THIS
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Then restart:
```bash
systemctl restart rivaflow-api
```

---

## Phase 10: DNS Configuration

### 10.1 Point Domain to VPS

In your domain registrar or DNS provider:

**A Record:**
```
Host: rivaflow (or @)
Value: YOUR_VPS_IP
TTL: 3600
```

**Wait 5-60 minutes for DNS propagation**

### 10.2 Verify DNS

```bash
dig rivaflow.yourdomain.com
# Should show your VPS IP
```

---

## Phase 11: Testing

### 11.1 Check All Services

```bash
systemctl status ollama
systemctl status rivaflow-api
systemctl status rivaflow-web
systemctl status nginx
```

### 11.2 Test Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Ollama
curl http://localhost:11434/api/tags
```

### 11.3 Access Application

Open browser: `https://rivaflow.yourdomain.com`

- Create account
- Login
- Test all features
- Test chat

---

## Maintenance Commands

### View Logs

```bash
# API logs
journalctl -u rivaflow-api -f

# Frontend logs
journalctl -u rivaflow-web -f

# Ollama logs
journalctl -u ollama -f

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Restart Services

```bash
systemctl restart rivaflow-api
systemctl restart rivaflow-web
systemctl restart ollama
systemctl restart nginx
```

### Update Application

```bash
cd /var/www/rivaflow

# Pull latest code
git pull origin main

# Update backend
cd rivaflow
source venv/bin/activate
pip install -r requirements.txt
systemctl restart rivaflow-api

# Update frontend
cd ../web
npm install
npm run build
systemctl restart rivaflow-web
```

### Database Backup

```bash
# Create backup
cp ~/.rivaflow/rivaflow.db ~/.rivaflow/rivaflow.db.backup.$(date +%Y%m%d)

# Set up daily backups (cron)
crontab -e
# Add: 0 2 * * * cp ~/.rivaflow/rivaflow.db ~/.rivaflow/rivaflow.db.backup.$(date +\%Y\%m\%d)
```

---

## Troubleshooting

### API Won't Start

```bash
journalctl -u rivaflow-api -n 50
# Check for Python errors, missing dependencies
```

### Chat Not Working

```bash
# Check Ollama
systemctl status ollama
ollama list

# Test Ollama directly
curl http://localhost:11434/api/chat -d '{"model":"llama3.2:3b","messages":[{"role":"user","content":"hi"}],"stream":false}'
```

### Frontend Not Loading

```bash
# Check if build exists
ls -la /var/www/rivaflow/web/dist

# Rebuild
cd /var/www/rivaflow/web
npm run build
systemctl restart rivaflow-web
```

### SSL Certificate Issues

```bash
certbot certificates
certbot renew --force-renewal
```

---

## Resource Monitoring

```bash
# Check RAM usage
free -h

# Check disk usage
df -h

# Check CPU
top

# Check Ollama memory
ps aux | grep ollama
```

---

## Expected Resource Usage

- **RAM:**
  - Ollama: ~2-3GB
  - API: ~100MB
  - Frontend: ~50MB
  - System: ~500MB
  - **Total: ~3-3.5GB / 4GB** ✅

- **Disk:**
  - Model: ~2GB
  - Application: ~500MB
  - System: ~2GB
  - **Total: ~5GB** ✅

- **CPU:**
  - Idle: <10%
  - During chat: 50-100%

---

## Security Checklist

- [ ] Changed default SSH port (optional)
- [ ] Disabled root SSH login (optional but recommended)
- [ ] Set up SSH key authentication
- [ ] UFW firewall enabled
- [ ] SSL/HTTPS configured
- [ ] Strong JWT secret key
- [ ] Regular backups configured
- [ ] Keep system updated: `apt update && apt upgrade`

---

## Next Steps After Deployment

1. Create your user account
2. Invite friends with registration link
3. Test all features
4. Monitor logs for errors
5. Set up backup automation
6. Consider upgrading to 8GB VPS if chat quality insufficient

---

**Estimated Deployment Time:** 2-3 hours
**Cost:** $0 extra (using existing VPS)
