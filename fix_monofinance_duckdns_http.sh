#!/bin/bash
echo "=== Configuring Nginx for monofinance.duckdns.org on HTTP (Port 80) ==="

sudo tee /etc/nginx/sites-available/monofinance > /dev/null << 'EOF'
server {
    listen 80;
    server_name monofinance.duckdns.org;

    location / {
        proxy_pass http://127.0.0.1:5001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo nginx -t && sudo systemctl reload nginx
echo "=== Done! monofinance.duckdns.org now serves MonoFinance directly on HTTP ==="
