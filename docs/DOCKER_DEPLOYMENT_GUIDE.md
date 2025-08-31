# MCP Crypto Trading Server - Docker Production Deployment Guide

## 🚀 Overview

This guide provides complete instructions for deploying the MCP Crypto Trading Server in a production Docker environment, specifically optimized for Kaayaan infrastructure integration.

## 📋 Prerequisites

- Docker Engine 20.10+ or Docker Desktop
- Docker Compose V2
- Minimum 2GB RAM, 4GB recommended
- 10GB available disk space
- Network access to Kaayaan infrastructure

## 🛠 Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp .env.production.example .env.production

# Edit with your actual credentials
nano .env.production
```

### 2. Build and Deploy

```bash
# Validate configuration
./validate_build.sh

# Build the Docker image
docker build -t mcp-crypto-trading:latest .

# Start all services
docker-compose -f docker-compose.production.yml up -d
```

### 3. Verify Deployment

```bash
# Check service status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f mcp-crypto-server

# Test health endpoint
curl http://localhost:8080/health
```

## 📁 File Structure

```
MCP-Crypto-T-project-main/
├── Dockerfile                      # Multi-stage production build
├── docker-compose.production.yml   # Complete service stack
├── docker-entrypoint.sh           # Container initialization
├── start_server.sh                # Production server launcher
├── requirements_mcp.txt            # Pinned dependencies
├── .env.production.example         # Environment template
├── validate_build.sh              # Build validation
├── mcp_crypto_server.py           # Main application
└── DOCKER_DEPLOYMENT_GUIDE.md     # This file
```

## 🔧 Configuration Details

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB connection | `mongodb://username:password@mongodb:27017/` |
| `REDIS_URL` | Redis connection | `redis://:password@redis:6379` |
| `POSTGRES_DSN` | PostgreSQL connection | `postgresql://user:password@postgresql:5432/database` |
| `WHATSAPP_API` | WhatsApp integration | `https://your-whatsapp-api.com` |
| `MCP_SERVER_PORT` | Server port | `8080` |

### Kaayaan Infrastructure Integration

The deployment is pre-configured for Kaayaan infrastructure with:

- **MongoDB**: Database storage for trading data
- **Redis**: Caching and session management
- **PostgreSQL**: Analytics and reporting
- **WhatsApp**: Notification integration
- **Monitoring**: Prometheus + Grafana stack

## 🐳 Docker Configuration

### Multi-Stage Build Benefits

1. **Optimized Size**: Builder stage discarded in final image
2. **Security**: Non-root user, minimal attack surface
3. **Performance**: Compiled dependencies, optimized layers
4. **Caching**: Efficient layer caching for faster builds

### Security Features

- Non-root user execution
- Read-only filesystem where possible
- Security updates applied
- Minimal runtime dependencies
- Proper signal handling

## 🔍 Health Checks

### Application Health

```bash
# Internal health check
curl http://localhost:8080/health

# Container health status
docker inspect mcp-crypto-trading --format='{{.State.Health.Status}}'
```

### Database Connections

The entrypoint script validates all database connections before starting:
- MongoDB connectivity test
- Redis ping verification
- PostgreSQL connection validation

## 📊 Monitoring

### Built-in Monitoring Stack

- **Prometheus**: Metrics collection (`http://localhost:9090`)
- **Grafana**: Visualization dashboard (`http://localhost:3000`)
- **ELK Stack**: Log aggregation and analysis

### Key Metrics

- Request rate and response times
- Database connection health
- Memory and CPU usage
- Error rates and alerts

### Log Management

```bash
# Application logs
docker-compose -f docker-compose.production.yml logs mcp-crypto-server

# All service logs
docker-compose -f docker-compose.production.yml logs

# Follow logs in real-time
docker-compose -f docker-compose.production.yml logs -f
```

## 🚦 Deployment Commands

### Development Mode

```bash
# Build without cache
docker build --no-cache -t mcp-crypto-trading:dev .

# Run with development overrides
docker-compose -f docker-compose.production.yml -f docker-compose.override.yml up
```

### Production Mode

```bash
# Production build with build args
docker build \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VCS_REF=$(git rev-parse HEAD) \
  --build-arg VERSION=1.0.0 \
  -t mcp-crypto-trading:1.0.0 \
  -t mcp-crypto-trading:latest .

# Deploy production stack
docker-compose -f docker-compose.production.yml up -d
```

### Scaling

```bash
# Scale MCP server instances
docker-compose -f docker-compose.production.yml up -d --scale mcp-crypto-server=3

# Scale with resource limits
docker-compose -f docker-compose.production.yml up -d \
  --scale mcp-crypto-server=2 \
  --scale redis=1 \
  --scale mongodb=1
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Container Won't Start

```bash
# Check logs for errors
docker logs mcp-crypto-trading

# Validate environment
docker run --rm -it --env-file .env.production mcp-crypto-trading:latest /bin/bash
```

#### 2. Database Connection Errors

```bash
# Test MongoDB connection
docker exec -it mcp-mongodb mongosh --eval "db.runCommand('ping')"

# Test Redis connection  
docker exec -it mcp-redis redis-cli ping

# Test PostgreSQL connection
docker exec -it mcp-postgresql pg_isready
```

#### 3. High Memory Usage

```bash
# Monitor resource usage
docker stats

# Check container resource limits
docker inspect mcp-crypto-trading --format='{{.HostConfig.Memory}}'

# Adjust limits in docker-compose.production.yml
```

#### 4. Network Connectivity

```bash
# Check container networking
docker network ls
docker network inspect mcp-crypto-t-project-main_kaayaan-network

# Test inter-container communication
docker exec -it mcp-crypto-trading ping mongodb
```

### Debug Mode

Enable debug logging:

```bash
# Set debug environment
export DEBUG=true
export LOG_LEVEL=DEBUG

# Rebuild with debug enabled
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d
```

## 📈 Performance Optimization

### Resource Allocation

```yaml
# Recommended resource limits
services:
  mcp-crypto-server:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
```

### Database Optimization

```bash
# MongoDB performance tuning
docker exec -it mcp-mongodb mongosh --eval "
  db.adminCommand({setParameter: 1, wiredTigerConcurrentReadTransactions: 64})
"

# Redis memory optimization
docker exec -it mcp-redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## 🔒 Security Checklist

- [ ] Change default passwords in `.env.production`
- [ ] Enable TLS/SSL certificates in nginx configuration
- [ ] Configure firewall rules for exposed ports
- [ ] Set up regular security updates
- [ ] Enable audit logging
- [ ] Configure backup encryption
- [ ] Review and rotate API keys regularly

## 🎯 Production Deployment Checklist

### Pre-Deployment
- [ ] Run `./validate_build.sh` successfully
- [ ] Configure `.env.production` with real credentials
- [ ] Test database connections
- [ ] Verify SSL certificates
- [ ] Set up monitoring alerts

### Deployment
- [ ] Build and tag Docker image
- [ ] Deploy to staging environment first
- [ ] Run integration tests
- [ ] Deploy to production
- [ ] Verify all health checks pass

### Post-Deployment
- [ ] Monitor logs for errors
- [ ] Verify metrics collection
- [ ] Test API endpoints
- [ ] Confirm backup processes
- [ ] Document deployment

## 🆘 Support

### Getting Help

1. Check application logs first
2. Verify environment configuration
3. Test individual service health
4. Review this deployment guide
5. Contact Kaayaan infrastructure team

### Useful Commands

```bash
# Complete system reset
docker-compose -f docker-compose.production.yml down -v
docker system prune -a
docker volume prune

# Backup important data
docker exec mcp-mongodb mongodump --archive=/backup/mongo-$(date +%Y%m%d).gz --gzip

# View container processes
docker exec -it mcp-crypto-trading ps aux

# Check network connectivity
docker exec -it mcp-crypto-trading netstat -tlnp
```

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-08-31 | Initial production release |

---

**Ready for Production Deployment! 🚀**

This MCP Crypto Trading Server is now fully configured for production deployment in the Kaayaan infrastructure environment.