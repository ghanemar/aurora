# Docker Setup for Aurora

Complete Docker configuration for running the Aurora platform with all services containerized.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│                   (aurora-network)                       │
│                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│  │ Frontend │◄───│ Backend  │◄───│PostgreSQL│         │
│  │  Nginx   │    │ FastAPI  │    │          │         │
│  │   :80    │    │  :8001   │    │  :5432   │         │
│  └──────────┘    └──────────┘    └──────────┘         │
│       │               │                                 │
│       │               └──────────►┌──────────┐         │
│       │                           │  Redis   │         │
│       │                           │  :6379   │         │
│       │                           └──────────┘         │
└───────┼─────────────────────────────────────────────────┘
        │
   Host Ports:
   - 3000 → Frontend
   - 8001 → Backend API
   - 5434 → PostgreSQL
   - 6381 → Redis
```

## Services

### 1. PostgreSQL Database
- **Image:** `postgres:15-alpine`
- **Port:** 5434:5432 (host:container)
- **Credentials:** aurora/aurora_dev
- **Volume:** Persistent storage for database

### 2. Redis Cache
- **Image:** `redis:7-alpine`
- **Port:** 6381:6379 (host:container)
- **Usage:** Caching and session storage

### 3. Backend API (FastAPI)
- **Build:** Custom Dockerfile
- **Port:** 8001:8001 (host:container)
- **Hot Reload:** Source code mounted for development
- **Dependencies:** PostgreSQL, Redis

### 4. Frontend (React + Nginx)
- **Build:** Multi-stage Dockerfile
- **Port:** 3000:80 (host:container)
- **Serves:** Production-optimized React build
- **Proxy:** API requests proxied to backend

## Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### 1. Start All Services

```bash
# Start all services in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 2. Run Database Migrations

```bash
# Access backend container
docker-compose exec backend bash

# Run migrations
poetry run alembic upgrade head

# Seed database (optional)
poetry run python scripts/seed_mvp_data.py

# Exit container
exit
```

### 3. Access Services

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8001
- **API Docs:** http://localhost:8001/docs
- **Health Check:** http://localhost:8001/health

**Login Credentials:**
- Username: `admin`
- Password: `admin123`

## Docker Commands

### Service Management

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart backend
docker-compose restart frontend

# View running services
docker-compose ps

# View service logs
docker-compose logs -f [service-name]
```

### Building

```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build backend
docker-compose build frontend

# Build with no cache
docker-compose build --no-cache
```

### Database Operations

```bash
# Access PostgreSQL
docker-compose exec postgres psql -U aurora -d aurora

# Backup database
docker-compose exec postgres pg_dump -U aurora aurora > backup.sql

# Restore database
docker-compose exec -T postgres psql -U aurora aurora < backup.sql
```

### Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove containers and volumes (⚠️ deletes data)
docker-compose down -v

# Remove containers, volumes, and images
docker-compose down -v --rmi all

# Prune unused Docker resources
docker system prune -a
```

## Development Workflow

### Hot Reload

Both backend and frontend support hot reload in development:

**Backend:**
- Source code mounted at `/app/src`
- Uvicorn runs with `--reload` flag
- Changes to Python files automatically restart server

**Frontend:**
- Production build served by Nginx
- Rebuild container to see changes: `docker-compose build frontend && docker-compose up -d frontend`

### Environment Variables

Create a `.env` file in project root:

```bash
# Security
SECRET_KEY=your-super-secret-key-change-in-production

# Database
DATABASE_URL=postgresql+asyncpg://aurora:aurora_dev@postgres:5432/aurora

# Redis
REDIS_URL=redis://redis:6379/0

# API
CORS_ORIGINS=http://localhost:3000,http://localhost
```

### Accessing Remote IP

If deploying to a remote server, update `CORS_ORIGINS` and access via:
- Frontend: `http://YOUR_SERVER_IP:3000`
- Backend: `http://YOUR_SERVER_IP:8001`

## Production Deployment

### 1. Update Environment Variables

```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env file
SECRET_KEY=<generated-key>
ENVIRONMENT=production
```

### 2. Use Production Compose File

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    command: uvicorn src.main:app --host 0.0.0.0 --port 8001 --workers 4
    environment:
      ENVIRONMENT: production
    volumes: []  # Remove source code mounts

  frontend:
    # Uses production nginx configuration
```

Run with:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 3. Enable HTTPS

Use a reverse proxy (Nginx/Caddy) or update frontend nginx config for SSL:

```nginx
listen 443 ssl http2;
ssl_certificate /etc/ssl/certs/cert.pem;
ssl_certificate_key /etc/ssl/private/key.pem;
```

## Troubleshooting

### Backend won't start

```bash
# Check logs
docker-compose logs backend

# Common issues:
# 1. Database not ready - wait for PostgreSQL health check
# 2. Missing migrations - run alembic upgrade head
# 3. Port conflict - check if 8001 is in use
```

### Frontend can't connect to API

```bash
# Verify backend is running
curl http://localhost:8001/health

# Check nginx proxy configuration
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf

# Verify CORS settings in backend
```

### Database connection errors

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U aurora -d aurora -c "SELECT 1;"

# Reset database (⚠️ deletes all data)
docker-compose down -v
docker-compose up -d postgres
# Wait for health check, then run migrations
```

### Permission errors

```bash
# If you see permission errors, fix ownership:
sudo chown -R $USER:$USER .
```

## Performance Optimization

### Backend

- Increase workers: `--workers 4` (CPU cores × 2-4)
- Enable Gunicorn: Replace uvicorn with gunicorn
- Use Redis for caching

### Frontend

- Enable gzip compression (already configured in nginx)
- Configure CDN for static assets
- Implement service worker for caching

### Database

- Tune PostgreSQL settings in `docker-compose.yml`:
  ```yaml
  command: >
    postgres
    -c shared_buffers=256MB
    -c effective_cache_size=1GB
    -c max_connections=100
  ```

## Monitoring

### Health Checks

All services have health checks configured:

```bash
# Check service health
docker-compose ps

# Manual health check
curl http://localhost:8001/health  # Backend
curl http://localhost:3000/        # Frontend
```

### Resource Usage

```bash
# View resource usage
docker stats

# View logs
docker-compose logs --tail=100 -f
```

## Next Steps

1. **Set up CI/CD:** Automate builds and deployments
2. **Configure monitoring:** Add Prometheus + Grafana
3. **Implement backups:** Automate database backups
4. **Add logging:** Centralized logging with ELK stack
5. **Security hardening:** Update secrets, enable HTTPS, configure firewall

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review health checks: `docker-compose ps`
3. Consult main README.md for application-specific help
