# 🛠️ Seedance V2 Manual Deployment Guide

This document provides a complete manual deployment process for deploying the Seedance V2 application after Terraform creates the infrastructure.

## 📋 Prerequisites

1. ✅ Infrastructure created via Terraform (ECS instance, network, security groups, etc.)
2. ✅ SSH private key file (usually `seedance-keypair.pem`)
3. ✅ Server's public IP address
4. ✅ BytePlus API key and base URL

---

## 🚀 Deployment Steps

### Step 1: Connect to Server

```bash
# Set private key permissions
chmod 400 seedance-keypair.pem

# SSH connect to server
ssh -i seedance-keypair.pem root@<SERVER_IP>
```

### Step 2: Update System and Install Dependencies

```bash
# Update system packages
apt-get update

# Install required system packages
apt-get install -y \
    nginx \
    python3 \
    python3-venv \
    python3-pip \
    supervisor \
    git \
    vim \
    htop \
    curl \
    wget \
    unzip

# Verify Python version
python3 --version
# Should show Python 3.12.x
```

### Step 3: Create Application Directory

```bash
# Create application directory
mkdir -p /opt/seedance-v2
cd /opt/seedance-v2

# Verify current directory
pwd
# Should show: /opt/seedance-v2
```

### Step 4: Download Application Files from GitHub

```bash
# Set GitHub raw file URL
GITHUB_BASE="https://raw.githubusercontent.com/kookliu/BP-Training-GenVideoWeb/main/seedance-v2"

# Download main application file
curl -L -o app.py "$GITHUB_BASE/app.py"

# Download dependencies file
curl -L -o requirements.txt "$GITHUB_BASE/requirements.txt"

# Download README file
curl -L -o README.md "$GITHUB_BASE/README.md"

# Verify downloaded files
ls -la
# Should see: app.py, requirements.txt, README.md
```

### Step 5: Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify virtual environment
echo $VIRTUAL_ENV
# Should show: /opt/seedance-v2/venv

# Upgrade pip
pip install --upgrade pip

# Install application dependencies
pip install -r requirements.txt
```

### Step 6: Configure Environment Variables

Create environment variables file:

```bash
# Create environment variables file
cat > .env << 'EOF'
ARK_API_KEY=your_byteplus_api_key_here
ARK_BASE_URL=https://ark.ap-southeast.bytepluses.com/api/v3
EOF

# Set file permissions (protect API key)
chmod 600 .env

# Verify environment variables file
cat .env
```

### Step 7: Test Application

```bash
# Test run application in background
source .env
export ARK_API_KEY ARK_BASE_URL

# Test if application can start normally
python3 app.py &

# Wait a few seconds
sleep 5

# Check if application is running
ps aux | grep app.py

# Check if port is listening
netstat -tlnp | grep 7860

# Stop test process
pkill -f app.py
```

### Step 8: Configure Nginx Reverse Proxy

```bash
# Create Nginx configuration file
cat > /etc/nginx/sites-available/seedance << 'EOF'
server {
    listen 80;
    server_name _;
    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:7860;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Gradio
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeout settings
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }
}
EOF

# Enable site configuration
ln -sf /etc/nginx/sites-available/seedance /etc/nginx/sites-enabled/

# Remove default site
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# Restart Nginx
systemctl restart nginx
systemctl enable nginx

# Check Nginx status
systemctl status nginx
```

### Step 9: Create systemd Service

```bash
# Create systemd service file
cat > /etc/systemd/system/seedance.service << 'EOF'
[Unit]
Description=Seedance V2 Video Generation Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/seedance-v2
Environment=ARK_API_KEY=your_byteplus_api_key_here
Environment=ARK_BASE_URL=https://ark.ap-southeast.bytepluses.com/api/v3
Environment=PYTHONPATH=/opt/seedance-v2
ExecStart=/opt/seedance-v2/venv/bin/python app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Resource limits
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

# ⚠️ Important: Edit service file, replace with real API key
nano /etc/systemd/system/seedance.service
# Replace "your_byteplus_api_key_here" with actual API key

# Reload systemd configuration
systemctl daemon-reload

# Enable and start service
systemctl enable seedance
systemctl start seedance

# Check service status
systemctl status seedance
```

### Step 10: Verify Deployment

```bash
# 1. Check service status
systemctl status seedance
systemctl status nginx

# 2. Check port listening
netstat -tlnp | grep -E "(80|7860)"

# 3. Check application logs
journalctl -u seedance -f --no-pager -n 20

# 4. Test local access
curl -I http://localhost
curl -I http://localhost:7860

# 5. Get public IP
curl -s ifconfig.me

# 6. Test external access (from local machine)
# curl -I http://PUBLIC_IP
# curl -I http://PUBLIC_IP:7860
```

---

## 🔧 Common Management Commands

### Service Management
```bash
# View service status
systemctl status seedance

# Restart service
systemctl restart seedance

# Stop service
systemctl stop seedance

# Start service
systemctl start seedance

# View service logs
journalctl -u seedance -f

# View recent error logs
journalctl -u seedance --since "1 hour ago" -p err
```

### Application Management
```bash
# Enter application directory
cd /opt/seedance-v2

# Activate virtual environment
source venv/bin/activate

# Update application code
curl -L -o app.py "https://raw.githubusercontent.com/kookliu/BP-Training-GenVideoWeb/main/seedance-v2/app.py"

# Update dependencies
pip install -r requirements.txt

# Restart service to apply updates
systemctl restart seedance
```

### Nginx Management
```bash
# Test Nginx configuration
nginx -t

# Restart Nginx
systemctl restart nginx

# View Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

---

## 🌐 Access Application

After deployment is complete, you can access the application via:

### Web Interface Access
- **Main access URL**: `http://PUBLIC_IP` (via Nginx proxy)
- **Direct access URL**: `http://PUBLIC_IP:7860` (direct Gradio access)

### SSH Management Access
```bash
ssh -i seedance-keypair.pem root@PUBLIC_IP
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Service Cannot Start
```bash
# View detailed error information
journalctl -u seedance -n 50

# Check Python environment
cd /opt/seedance-v2
source venv/bin/activate
python3 app.py
```

#### 2. Port Cannot Be Accessed
```bash
# Check firewall (Ubuntu disabled by default)
ufw status

# Check port listening
netstat -tlnp | grep -E "(80|7860)"

# Check security group settings (in BytePlus console)
```

#### 3. API Key Error
```bash
# Check environment variables
systemctl show seedance --property=Environment

# Update API key
nano /etc/systemd/system/seedance.service
systemctl daemon-reload
systemctl restart seedance
```

#### 4. Virtual Environment Issues
```bash
# Recreate virtual environment
cd /opt/seedance-v2
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
systemctl restart seedance
```

---

## 📝 Configuration File Locations

| File/Directory | Path | Description |
|----------------|------|-------------|
| Application Directory | `/opt/seedance-v2` | Main application directory |
| Python Virtual Environment | `/opt/seedance-v2/venv` | Python virtual environment |
| Systemd Service | `/etc/systemd/system/seedance.service` | Service configuration file |
| Nginx Configuration | `/etc/nginx/sites-available/seedance` | Nginx site configuration |
| Application Logs | `journalctl -u seedance` | System logs |
| Nginx Logs | `/var/log/nginx/` | Nginx access and error logs |

---

## ✅ Deployment Checklist

After deployment is complete, confirm all the following items are working:

- [ ] SSH can connect to server normally
- [ ] Python 3.12 environment works properly
- [ ] Application files downloaded successfully from GitHub
- [ ] Python virtual environment created successfully
- [ ] Dependencies installed successfully
- [ ] Environment variables configured correctly
- [ ] Nginx configured correctly and running
- [ ] Systemd service created and running
- [ ] Ports 80 and 7860 listening normally
- [ ] Application accessible via public IP
- [ ] Application functions normally (can generate videos)

Congratulations! You have successfully manually deployed the Seedance V2 application! 🎉