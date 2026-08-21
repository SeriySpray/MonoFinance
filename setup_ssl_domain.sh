#!/bin/bash
# Setup permanent Let's Encrypt SSL certificate for monofinance.duckdns.org

echo "=== Configuring Nginx for monofinance.duckdns.org ==="

sudo tee /etc/nginx/sites-available/camerastream > /dev/null << 'NGINX_EOF'
server {
    listen 80;
    server_name monofinance.duckdns.org;

    location = /monofinance {
        return 301 /monofinance/;
    }

    location /monofinance/ {
        proxy_pass http://127.0.0.1:5001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
NGINX_EOF

sudo nginx -t && sudo systemctl reload nginx

echo "=== Requesting Let's Encrypt SSL Certificate ==="
sudo /snap/bin/certbot --nginx -d monofinance.duckdns.org --non-interactive --agree-tos -m admin@mono.finance --redirect

echo "=== SSL Configuration Complete ==="
