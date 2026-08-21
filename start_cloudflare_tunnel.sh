#!/bin/bash
echo "=== Starting Cloudflare Tunnel Service ==="
sudo tee /etc/systemd/system/cloudflared-monofinance.service > /dev/null << 'EOF'
[Unit]
Description=Cloudflare Tunnel for MonoFinance HTTPS
After=network.target

[Service]
ExecStart=/usr/local/bin/cloudflared tunnel --url http://127.0.0.1:5001
Restart=on-failure
RestartSec=10s
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable cloudflared-monofinance
sudo systemctl restart cloudflared-monofinance

sleep 5
echo "=== Tunnel Started! Active HTTPS URL: ==="
sudo journalctl -u cloudflared-monofinance -n 30 | grep trycloudflare.com
