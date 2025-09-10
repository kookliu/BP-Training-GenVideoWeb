#!/bin/bash

# Update system and install packages
apt-get update
apt-get install -y curl wget git nginx python3 python3-pip python3-venv

# Create application directory
mkdir -p /opt/seedance-v2
cd /opt/seedance-v2

# Create environment file with API configuration
cat > .env <<'EOF'
ARK_API_KEY=ARK_API_KEY_PLACEHOLDER
ARK_BASE_URL=ARK_BASE_URL_PLACEHOLDER
MODEL_SEEDANCE_PRO_API=MODEL_PRO_PLACEHOLDER
MODEL_SEEDANCE_LITE_T2V_API=MODEL_LITE_T2V_PLACEHOLDER
MODEL_SEEDANCE_LITE_I2V_API=MODEL_LITE_I2V_PLACEHOLDER
EOF

# Download application files from GitHub
echo "Downloading Seedance application from GitHub..."

# Download the main application file
wget -O app.py https://raw.githubusercontent.com/kookliu/BP-Training-GenVideoWeb/main/ubuntu-seedance-v2/seedance-app.py

# Download requirements.txt
wget -O requirements.txt https://raw.githubusercontent.com/kookliu/BP-Training-GenVideoWeb/main/ubuntu-seedance-v2/seedance-requirements.txt

# Verify downloads
if [ ! -f "app.py" ] || [ ! -f "requirements.txt" ]; then
    echo "Failed to download application files from GitHub"
    echo "Creating fallback simple application..."
    
    # Create fallback requirements.txt
    cat > requirements.txt <<'EOF'
gradio==4.44.0
requests==2.31.0
pillow==10.0.1
python-dotenv==1.0.0
EOF

    # Create fallback simple app
    cat > app.py <<'EOF'
import gradio as gr
import os
from dotenv import load_dotenv

load_dotenv()

def test_api_config():
    api_key = os.getenv("ARK_API_KEY", "Not configured")
    base_url = os.getenv("ARK_BASE_URL", "Not configured")
    pro_model = os.getenv("MODEL_SEEDANCE_PRO_API", "Not configured")
    return f"API Key: {api_key[:20]}...\nBase URL: {base_url}\nPro Model: {pro_model}"

with gr.Blocks(title="Seedance V2") as demo:
    gr.Markdown("# 🎬 Seedance V2 - AI Video Generation")
    gr.Markdown("**GitHub Download Failed - Running Fallback Version**")
    
    test_btn = gr.Button("Test API Configuration")
    test_output = gr.Textbox(label="Configuration", lines=5)
    test_btn.click(test_api_config, outputs=test_output)

demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
EOF
fi

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create systemd service
cat > /etc/systemd/system/seedance-v2.service <<'EOF'
[Unit]
Description=Seedance V2 Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/seedance-v2
Environment="PATH=/opt/seedance-v2/venv/bin"
ExecStart=/opt/seedance-v2/venv/bin/python /opt/seedance-v2/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
cat > /etc/nginx/sites-available/seedance-v2 <<'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:7860;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 100M;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/seedance-v2 /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Start services
systemctl daemon-reload
systemctl enable seedance-v2.service
systemctl start seedance-v2.service
systemctl restart nginx
systemctl enable nginx

# Log deployment completion
echo "Seedance V2 GitHub deployment completed at $(date)" >> /var/log/deployment.log
echo "Application available at: http://$(curl -s ifconfig.me)" >> /var/log/deployment.log
echo "Direct Gradio: http://$(curl -s ifconfig.me):7860" >> /var/log/deployment.log