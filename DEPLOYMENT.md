# Deployment Guide: GitHub Actions → Hetzner

## Was wurde erstellt

| Datei | Zweck |
|---|---|
| `.gitignore` | EDIFACT-Dateien + DB ergänzt |
| `docker-compose.prod.yml` | Hetzner-Version: Image aus ghcr.io, named volumes statt Datei-Mounts |
| `.github/workflows/deploy.yml` | CI/CD Pipeline |

---

## Einmaliger Setup

### 1. GitHub Repository erstellen

```bash
cd /home/alex/kk_info
git init
git add .
git commit -m "Initial commit"
# Auf github.com ein neues Repo erstellen, z.B. "kk-info"
git remote add origin https://github.com/DEIN_USER/kk-info.git
git push -u origin main
```

### 2. GitHub Secrets setzen

Unter `github.com/DEIN_USER/kk-info → Settings → Secrets and variables → Actions`:

| Secret | Wert |
|---|---|
| `HETZNER_HOST` | IP oder Domain des Hetzner-Servers |
| `HETZNER_USER` | SSH-User (z.B. `root`) |
| `SSH_PRIVATE_KEY` | Inhalt des privaten SSH-Keys (`cat ~/.ssh/id_ed25519`) |

### 3. Auf dem Hetzner-Server (einmalig)

```bash
# Deployment-Verzeichnis anlegen
mkdir -p /opt/kk-info

# EDIFACT-Rohdaten hochladen (von lokalem Rechner aus)
scp -r kostentraegerdateien/ root@HETZNER_IP:/opt/kk-info/

# Nach dem ersten Deploy: DB auf dem Server befüllen
docker exec kk-info-api python import_edifact.py kostentraegerdateien/01_2026/EK05Q126.ke0 --clear
docker exec kk-info-api python import_edifact.py kostentraegerdateien/01_2026/AO05Q126.ke0
docker exec kk-info-api python import_edifact.py kostentraegerdateien/01_2026/BK05Q126.ke1
docker exec kk-info-api python import_edifact.py kostentraegerdateien/01_2026/BN05Q325.ke1
docker exec kk-info-api python import_edifact.py kostentraegerdateien/01_2026/IK05Q425.ke0
docker exec kk-info-api python import_edifact.py kostentraegerdateien/01_2026/LK05Q425.ke0
```

### 4. Nginx auf Hetzner konfigurieren

```nginx
location /kk-info/ {
    proxy_pass http://localhost:9000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

Oder als eigene Domain/Subdomain:

```nginx
server {
    server_name kk-info.gehrer.click;
    location / {
        proxy_pass http://localhost:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Wie der Workflow läuft

```
git push → GitHub Actions startet
    │
    ├─ Job 1: Build & Push
    │    docker build → Push zu ghcr.io/DEIN_USER/kk-info:latest
    │
    └─ Job 2: Deploy (läuft nach Job 1)
         SCP: docker-compose.prod.yml + solr_config/ → Server
         SSH: docker compose pull && docker compose up -d
              docker image prune -f
```

Der DB-Inhalt auf dem Server bleibt erhalten (named volume `kk-info-db-data`),
nur der App-Code wird bei jedem Push aktualisiert.

---

## Wichtiger Unterschied: dev vs. prod Compose

| | `docker-compose.yml` (lokal) | `docker-compose.prod.yml` (Hetzner) |
|---|---|---|
| Image | wird lokal gebaut | wird von ghcr.io gepullt |
| Datenbank | `./kk_info.db` (Datei-Mount) | named volume `kk-info-db-data` |
| EDIFACT-Dateien | `./kostentraegerdateien/` gemountet | nicht gemountet |
| Ports | 9000, 8983 extern | nur 9000 extern |
