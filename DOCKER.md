# Docker Deployment

## Quick Start

```bash
# Build and start
docker-compose up -d

# Check logs
docker-compose logs -f

# Test API
curl http://localhost:9000/health
curl "http://localhost:9000/find-billing-center?krankenkasse=Techniker"
```

## Initial Setup

### 1. Build the image

```bash
docker-compose build
```

### 2. Start the container

```bash
docker-compose up -d
```

The API will be available at http://localhost:9000

### 3. Import data (if database is empty)

```bash
# Enter the container
docker-compose exec kk-info-api bash

# Import all files
python import_edifact.py kostentraegerdateien/01_2026/EK05Q126.ke0 --clear
python import_edifact.py kostentraegerdateien/01_2026/AO05Q126.ke0
python import_edifact.py kostentraegerdateien/01_2026/BK05Q126.ke1
python import_edifact.py kostentraegerdateien/01_2026/BN05Q325.ke1
python import_edifact.py kostentraegerdateien/01_2026/IK05Q425.ke0
python import_edifact.py kostentraegerdateien/01_2026/LK05Q425.ke0

# Exit container
exit
```

**Or** import before starting Docker (recommended):
```bash
# Use existing database
# Just make sure kk_info.db exists with data before docker-compose up
```

## Common Commands

### View logs
```bash
docker-compose logs -f
docker-compose logs -f kk-info-api
```

### Restart service
```bash
docker-compose restart
```

### Stop service
```bash
docker-compose down
```

### Rebuild after code changes
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Access container shell
```bash
docker-compose exec kk-info-api bash
```

### Check health
```bash
docker-compose ps
curl http://localhost:9000/health
```

## Volumes

The docker-compose.yml mounts:

1. **Database**: `./kk_info.db:/data/kk_info.db`
   - Persistent storage for the SQLite database
   - Survives container restarts

2. **Data files**: `./kostentraegerdateien:/app/kostentraegerdateien:ro`
   - Read-only access to EDIFACT files
   - Allows re-import without rebuilding

## Environment Variables

You can override settings in docker-compose.yml:

```yaml
environment:
  - DATABASE_URL=sqlite:////data/kk_info.db
  - LOG_LEVEL=info
```

## Production Deployment

### Using existing database

The simplest approach:
1. Import data locally first
2. Start Docker with existing database

```bash
# 1. Import data locally (if not done)
source venv/bin/activate
python import_edifact.py kostentraegerdateien/01_2026/*.ke* --clear

# 2. Start Docker (will use existing kk_info.db)
docker-compose up -d
```

### Behind reverse proxy (Nginx/Traefik)

Add labels to docker-compose.yml for your reverse proxy. Example for Traefik:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.kk-info.rule=Host(`kk-info.example.com`)"
  - "traefik.http.services.kk-info.loadbalancer.server.port=9000"
```

## Troubleshooting

### Container won't start
```bash
docker-compose logs
```

### Port already in use
Change port in docker-compose.yml:
```yaml
ports:
  - "9001:9000"  # Use 9001 on host
```

### Database permission issues
```bash
chmod 666 kk_info.db
```

### Import data into running container
```bash
docker-compose exec kk-info-api python import_edifact.py kostentraegerdateien/01_2026/EK05Q126.ke0
```

## API Endpoints

Once running, access:

- **API**: http://localhost:9000
- **Swagger UI**: http://localhost:9000/docs
- **ReDoc**: http://localhost:9000/redoc
- **Health**: http://localhost:9000/health

## Updating to New Data

When new monthly data arrives:

```bash
# 1. Stop container
docker-compose down

# 2. Import new data locally
source venv/bin/activate
python import_edifact.py kostentraegerdateien/02_2026/EK05Q126.ke0 --clear
python import_edifact.py kostentraegerdateien/02_2026/AO05Q126.ke0
# ... etc

# 3. Restart container
docker-compose up -d
```

Or import directly in container:
```bash
docker-compose exec kk-info-api python import_edifact.py kostentraegerdateien/02_2026/EK05Q126.ke0 --clear
```
