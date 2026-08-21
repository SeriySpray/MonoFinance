#!/bin/bash
# Setup Cloudflare HTTPS Tunnel for MonoFinance on Oracle Cloud
# Run this script on the Oracle Cloud VPS via SSH

echo "=== Installing Cloudflare Tunnel (cloudflared) ==="

ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    DOWNLOAD_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb"
else
    DOWNLOAD_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb"
fi

echo "Detected architecture: $ARCH. Downloading $DOWNLOAD_URL..."
curl -L --output cloudflared.deb "$DOWNLOAD_URL"
sudo dpkg -i cloudflared.deb || sudo apt-get install -f -y

# Create systemd service for Cloudflare quick tunnel to MonoFinance
echo "Configuring Cloudflare Tunnel service..."
sudo tee /etc/systemd/system/cloudflared-monofinance.service > /dev/null << 'EOF'
[Unit]
Description=Cloudflare Tunnel for MonoFinance HTTPS
After=network.target

[Service]
ExecStart=/usr/bin/cloudflared tunnel --url http://127.0.0.1:5001
Restart=always
RestartSec=5s
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable cloudflared-monofinance
sudo systemctl restart cloudflared-monofinance

sleep 4
echo "=== Cloudflare Tunnel Started! ==="
echo "Public HTTPS URL:"
sudo journalctl -u cloudflared-monofinance -n 25 | grep trycloudflare.com
