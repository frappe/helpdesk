# PM2 Production Guide

## Quick Start

### Start Application
```bash
# Build the application first
npm run build

# Start with PM2
pm2 start ecosystem.config.js

# Or use npm script
npm run pm2:start
```

### Monitor Application
```bash
# Real-time monitoring dashboard
pm2 monit

# List all processes
pm2 list

# Show specific app details
pm2 show helpdesk-api

# View logs
pm2 logs helpdesk-api

# View only errors
pm2 logs helpdesk-api --err

# Clear logs
pm2 flush
```

### Manage Application
```bash
# Restart application
pm2 restart helpdesk-api

# Reload (zero-downtime restart)
pm2 reload helpdesk-api

# Stop application
pm2 stop helpdesk-api

# Delete from PM2
pm2 delete helpdesk-api

# Restart all
pm2 restart all
```

## Auto-Start on System Boot

### Setup Startup Script
```bash
# Generate startup script
pm2 startup

# Save current process list
pm2 save

# To disable
pm2 unstartup
```

## Logs

### Log Locations
- Error logs: `./logs/pm2-error.log`
- Output logs: `./logs/pm2-out.log`

### Log Rotation
```bash
# Install PM2 log rotate module
pm2 install pm2-logrotate

# Configure log rotation
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7
pm2 set pm2-logrotate:compress true
```

## Cluster Mode

The app is configured to run in cluster mode with all CPU cores:

```javascript
instances: 'max',  // Use all CPU cores
exec_mode: 'cluster'
```

Benefits:
- Load balancing across cores
- Zero-downtime reloads
- Better performance
- Auto-restart on crash

## Environment Variables

### Production
```bash
pm2 start ecosystem.config.js --env production
```

### Development
```bash
pm2 start ecosystem.config.js --env development
```

## Monitoring & Metrics

### Built-in Monitoring
```bash
pm2 monit
```

### Web Dashboard (PM2 Plus - Optional)
```bash
# Free tier available
pm2 link <secret_key> <public_key>
```

### Custom Metrics
The application can send custom metrics to PM2:

```typescript
import pm2 from '@pm2/io';

const meter = pm2.meter({
  name: 'req/min',
  samples: 60
});

// Mark metric
meter.mark();
```

## Performance Tuning

### Memory Management
```javascript
max_memory_restart: '1G'  // Restart if exceeds 1GB
```

### Instance Count
```bash
# Specific number of instances
pm2 start ecosystem.config.js -i 4

# Auto-scale based on load
pm2 scale helpdesk-api +2  // Add 2 instances
pm2 scale helpdesk-api 4    // Set to 4 instances
```

## Useful Commands

```bash
# Update PM2
npm install pm2 -g

# Reset restart counter
pm2 reset helpdesk-api

# Reload all apps
pm2 reload all

# Graceful reload
pm2 reload helpdesk-api --update-env

# Send system signal
pm2 sendSignal SIGUSR2 helpdesk-api

# Generate process file
pm2 ecosystem
```

## NPM Scripts

Add to `package.json`:

```json
{
  "scripts": {
    "pm2:start": "pm2 start ecosystem.config.js --env production",
    "pm2:dev": "pm2 start ecosystem.config.js --env development",
    "pm2:stop": "pm2 stop helpdesk-api",
    "pm2:restart": "pm2 restart helpdesk-api",
    "pm2:reload": "pm2 reload helpdesk-api",
    "pm2:delete": "pm2 delete helpdesk-api",
    "pm2:logs": "pm2 logs helpdesk-api",
    "pm2:monit": "pm2 monit"
  }
}
```

## Troubleshooting

### App Won't Start
```bash
# Check PM2 logs
pm2 logs helpdesk-api --lines 100

# Check error logs
cat logs/pm2-error.log
```

### High Memory Usage
```bash
# Check memory
pm2 list

# Restart to clear memory
pm2 restart helpdesk-api
```

### App Keeps Crashing
```bash
# Check logs for errors
pm2 logs helpdesk-api --err

# Increase restart delay
pm2 restart helpdesk-api --min-uptime 10000
```
