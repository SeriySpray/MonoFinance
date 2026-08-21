#!/bin/bash
echo "=== Setting up Ngrok systemd service ==="
sudo tee /etc/systemd/system/ngrok-monofinance.service > /dev/null << 'EOF'
[Unit]
Description=Ngrok Tunnel for MonoFinance HTTPS
After=network.target

[Service]
ExecStart=/usr/local/bin/ngrok http 5001 --log stdout
Restart=always
RestartSec=5s
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ngrok-monofinance
sudo systemctl restart ngrok-monofinance

sleep 4
echo "=== Ngrok Started! ==="
