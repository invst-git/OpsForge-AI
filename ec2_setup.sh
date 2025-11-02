#!/bin/bash
# EC2 Setup Script - Run on fresh Ubuntu 22.04 instance

set -e

echo "Installing dependencies..."
sudo apt update
sudo apt install -y python3.10 python3-pip nodejs npm nginx git

echo "Creating app directory..."
sudo mkdir -p /opt/opsforge
sudo chown -R ubuntu:ubuntu /opt/opsforge

echo "Installing Python packages..."
cd /opt/opsforge
pip3 install fastapi uvicorn boto3 pydantic networkx anthropic python-dotenv

echo "Installing Node packages..."
cd /opt/opsforge/frontend
npm install
npm run build

echo "Configuring nginx..."
sudo tee /etc/nginx/sites-available/opsforge > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;

    # Frontend
    location / {
        root /opt/opsforge/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API proxy
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF

sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/opsforge /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

echo "Creating systemd service for backend..."
sudo tee /etc/systemd/system/opsforge-backend.service > /dev/null <<'EOF'
[Unit]
Description=OpsForge Backend API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/opsforge
Environment="PATH=/home/ubuntu/.local/bin:/usr/local/bin:/usr/bin:/bin"
Environment="AWS_REGION=us-east-1"
Environment="STRANDS_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0"
Environment="ENVIRONMENT=production"
Environment="CORS_ORIGIN=*"
ExecStart=/usr/bin/python3 backend_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable opsforge-backend
sudo systemctl start opsforge-backend

echo "Creating systemd service for data generator..."
sudo tee /etc/systemd/system/opsforge-generator.service > /dev/null <<'EOF'
[Unit]
Description=OpsForge Live Data Generator
After=network.target opsforge-backend.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/opsforge
Environment="PATH=/home/ubuntu/.local/bin:/usr/local/bin:/usr/bin:/bin"
Environment="AWS_REGION=us-east-1"
Environment="STRANDS_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0"
ExecStart=/usr/bin/python3 live_data_generator.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable opsforge-generator
sudo systemctl start opsforge-generator

echo "Setup complete!"
echo ""
echo "Services status:"
sudo systemctl status opsforge-backend --no-pager
sudo systemctl status opsforge-generator --no-pager
sudo systemctl status nginx --no-pager
echo ""
echo "Access application at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
