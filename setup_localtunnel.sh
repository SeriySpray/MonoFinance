#!/bin/bash
echo "=== Installing and configuring localtunnel ==="
sudo npm install -g localtunnel

sudo tee /etc/systemd/system/localtunnel-monofinance.service > /dev/null << 'EOF'
[Unit]
Description=Localtunnel for MonoFinance HTTPS
After=network.target

[Service]
ExecStart=/usr/local/bin/lt --port 5001 --subdomain monofinance-app-2026
Restart=always
RestartSec=5s
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable localtunnel-monofinance
sudo systemctl restart localtunnel-monofinance

sleep 3
echo "=== Localtunnel Started! ==="
