#!/bin/bash
sudo tee /etc/nginx/sites-available/camerastream > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    location = /monofinance {
        return 301 /monofinance/;
    }

    location /monofinance/ {
        proxy_pass http://127.0.0.1:5001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

sudo nginx -t && sudo systemctl reload nginx
echo "Nginx restored!"
