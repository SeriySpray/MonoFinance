#!/bin/bash
echo "=== Enabling SSL (HTTPS) on Nginx for monofinance.duckdns.org ==="

sudo tee /etc/nginx/sites-available/monofinance > /dev/null << 'EOF'
server {
    listen 80;
    server_name monofinance.duckdns.org;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name monofinance.duckdns.org;

    ssl_certificate /etc/letsencrypt/live/monofinance.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/monofinance.duckdns.org/privkey.pem;

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
echo "=== Nginx reloaded with SSL configuration! ==="
