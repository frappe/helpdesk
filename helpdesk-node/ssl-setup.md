# HTTPS/SSL Setup Guide

## For Production (with Let's Encrypt)

### Prerequisites:
- A domain name pointing to your server (e.g., helpdesk.yourdomain.com)
- Ports 80 and 443 open on your server

### Step 1: Install Certbot
```bash
sudo apt update
sudo apt install certbot
```

### Step 2: Get SSL Certificate
```bash
sudo certbot certonly --standalone -d helpdesk.yourdomain.com
```

### Step 3: Configure Backend for HTTPS

Update `helpdesk-node/src/server.ts`:

```typescript
import https from 'https';
import fs from 'fs';

const httpsOptions = {
  key: fs.readFileSync('/etc/letsencrypt/live/helpdesk.yourdomain.com/privkey.pem'),
  cert: fs.readFileSync('/etc/letsencrypt/live/helpdesk.yourdomain.com/fullchain.pem')
};

// Create HTTPS server instead of HTTP
const httpsServer = https.createServer(httpsOptions, app);
httpsServer.listen(443, () => {
  logger.info('🔒 HTTPS Server running on port 443');
});
```

### Step 4: Auto-renewal
```bash
# Add to crontab
sudo crontab -e

# Add this line to renew every 12 hours
0 */12 * * * certbot renew --quiet
```

## For Development (Self-Signed Certificate)

### Generate Self-Signed Certificate:
```bash
cd helpdesk-node
mkdir -p certs
openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes
```

### Use in Development:
See `src/config/https.config.ts` for development HTTPS setup.

## Environment Variables

Add to `.env`:
```
# SSL Configuration
SSL_ENABLED=true
SSL_KEY_PATH=/etc/letsencrypt/live/helpdesk.yourdomain.com/privkey.pem
SSL_CERT_PATH=/etc/letsencrypt/live/helpdesk.yourdomain.com/fullchain.pem

# Or for development
SSL_KEY_PATH=./certs/key.pem
SSL_CERT_PATH=./certs/cert.pem
```

## Nginx Reverse Proxy (Recommended)

Instead of handling SSL in Node.js, use Nginx:

```nginx
server {
    listen 80;
    server_name helpdesk.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name helpdesk.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/helpdesk.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/helpdesk.yourdomain.com/privkey.pem;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Proxy to Node.js backend
    location /api {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Serve React frontend
    location / {
        root /var/www/helpdesk/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

## Security Headers

Already configured in `src/middleware/security.ts` with Helmet.js
