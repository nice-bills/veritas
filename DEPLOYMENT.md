# Veritas Production Deployment Guide

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git repository cloned
- Environment variables configured
- Domain name (for production with SSL)

### 1. Environment Setup

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```bash
# Required: Coinbase Developer Platform API Keys
CDP_API_KEY_ID=organizations/xxx/apiKeys/xxx
CDP_API_KEY_SECRET=-----BEGIN EC PRIVATE KEY-----
...
-----END EC PRIVATE KEY-----

# Required: MiniMax API Key for AI brain
MINIMAX_API_KEY=sk-xxx

# Required: Database encryption key
ENCRYPTION_KEY=your-secure-encryption-key-min-32-chars-long

# Required: Database password
POSTGRES_PASSWORD=secure-password-here

# Optional: Wallet private key (if using existing wallet)
AGENT_PRIVATE_KEY=0x...

# Optional: Production domain
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 2. Development Deployment

Start all services in development mode with hot-reload:

```bash
# Start development environment
docker compose -f docker-compose.dev.yml up -d

# View logs
docker compose -f docker-compose.dev.yml logs -f

# Stop
docker compose -f docker-compose.dev.yml down
```

Access points:
- Frontend: http://localhost:3001
- Backend API: http://localhost:8001
- Database: localhost:5432

### 3. Production Deployment

#### Option A: Using Deploy Script

```bash
# Make script executable
chmod +x scripts/deploy.sh

# Deploy
./scripts/deploy.sh production
```

#### Option B: Manual Docker Compose

```bash
# Build and start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

Access points:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

### 4. Database Migrations

The backend will automatically create tables on startup. To manually initialize:

```bash
# Run database initialization
docker compose exec backend python -c "
import asyncio
from src.veritas.database import init_db
asyncio.run(init_db())
print('Database initialized')
"
```

### 5. SSL/HTTPS Setup (Production)

For production with SSL, use the nginx profile:

```bash
# Create nginx configuration
mkdir -p nginx/ssl

# Copy your SSL certificates
# - nginx/ssl/cert.pem (certificate)
# - nginx/ssl/key.pem (private key)

# Start with nginx
docker compose --profile nginx up -d
```

Example nginx.conf:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream frontend {
        server frontend:3000;
    }
    
    upstream backend {
        server backend:8000;
    }
    
    server {
        listen 80;
        server_name yourdomain.com;
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen 443 ssl;
        server_name yourdomain.com;
        
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        
        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }
        
        location /api {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        location /ws {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

## 📋 Service Overview

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | Next.js React app |
| Backend | 8000 | FastAPI Python server |
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Caching & sessions |
| Nginx | 80/443 | Reverse proxy (optional) |

## 🔧 Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `CDP_API_KEY_ID` | Coinbase Developer Platform API key ID |
| `CDP_API_KEY_SECRET` | CDP API private key |
| `MINIMAX_API_KEY` | MiniMax AI API key |
| `ENCRYPTION_KEY` | Fernet encryption key (32+ chars) |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_PASSWORD` | veritas | Database password |
| `ENABLE_MAINNET` | false | Enable mainnet (production only) |
| `DEBUG` | false | Debug mode |
| `CORS_ORIGINS` | localhost | Allowed CORS origins |

## 🛠️ Maintenance

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
```

### Update Services

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker compose up -d --build
```

### Backup Database

```bash
# Create backup
docker compose exec postgres pg_dump -U veritas veritas > backup.sql

# Restore backup
docker compose exec -T postgres psql -U veritas veritas < backup.sql
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3000/api/health
```

## 🚨 Troubleshooting

### Services Won't Start

1. Check logs: `docker compose logs -f`
2. Verify .env file exists and has correct values
3. Ensure ports are not in use: `lsof -i :8000`

### Database Connection Issues

1. Check PostgreSQL is running: `docker compose ps`
2. Verify DATABASE_URL in .env
3. Check database logs: `docker compose logs postgres`

### Frontend Won't Connect to API

1. Check NEXT_PUBLIC_API_URL in docker-compose.yml
2. Verify CORS_ORIGINS includes your domain
3. Check backend health: `curl http://localhost:8000/`

### WebSocket Connection Fails

1. Verify WEBSOCKET_TOKEN is set correctly
2. Check firewall rules for WebSocket port
3. Ensure nginx proxy configuration includes /ws location

## 📊 Monitoring

### Docker Stats

```bash
docker stats
```

### Resource Usage

```bash
# Check disk usage
docker system df

# Clean up unused images
docker system prune
```

## 🔐 Security Checklist

- [ ] Change default passwords in .env
- [ ] Use strong ENCRYPTION_KEY (32+ characters)
- [ ] Enable HTTPS in production
- [ ] Restrict CORS_ORIGINS to your domain only
- [ ] Set up firewall rules
- [ ] Regularly update Docker images
- [ ] Enable database backups
- [ ] Review and rotate API keys periodically

## 📝 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
