# TV Viewer Web 📺

[![GitHub Release](https://img.shields.io/github/v/release/tv-viewer-app/tv_viewer)](https://github.com/tv-viewer-app/tv_viewer/releases/latest)
[![Docker Image Size](https://img.shields.io/docker/image-size/asummoner/tvviewerapp/latest)](https://hub.docker.com/r/asummoner/tvviewerapp)
[![Docker Pulls](https://img.shields.io/docker/pulls/asummoner/tvviewerapp)](https://hub.docker.com/r/asummoner/tvviewerapp)

**Lightweight IPTV streaming web interface with 16,000+ channels. Perfect for NAS devices, home servers, and self-hosted media setups.**

🌐 **[Project Homepage](https://tv-viewer-app.github.io/tv_viewer/)** | 📦 **[Source Code](https://github.com/tv-viewer-app/tv_viewer)** | 📋 **[Changelog](https://github.com/tv-viewer-app/tv_viewer/blob/master/CHANGELOG.md)**

---

## What is TV Viewer?

TV Viewer is a self-hosted web application that aggregates free-to-air IPTV streams from around the world into a beautiful, modern interface. Deploy it on your NAS or any Docker host and watch live TV from any browser — no app installs, no subscriptions, no VLC required.

**Why use TV Viewer?**
- **Zero configuration** — launches with 16,000+ channels pre-loaded
- **Runs anywhere** — Synology, QNAP, Unraid, TrueNAS, Raspberry Pi, any Docker host
- **Tiny footprint** — under 50 MB RAM, 0.1 CPU core minimum
- **Browser-based** — works on phones, tablets, smart TVs, laptops
- **Privacy-first** — no accounts, no tracking, no cloud dependency

## Quick Start

```bash
docker run -d --name tv-viewer -p 8765:8765 -v tv-viewer-data:/data --restart unless-stopped asummoner/tvviewerapp
```

Then open **http://your-server-ip:8765** in any browser. That's it!

## Features

- 🌍 **16,000+ live TV channels** from 55+ countries
- 🎬 **In-browser HLS playback** — no VLC or external player needed
- 🔀 **Multi-source failover** — automatically switches to backup streams
- 📡 **Built-in CORS proxy** — plays streams that normally block browsers
- 🗺️ **Interactive world map** — browse channels by country
- 🔤 **A-Z sorted channels** — easy to find what you want
- ❤️ **Favorites** with server-side persistence
- 📊 **Health tracking** — broken channels filtered automatically
- 📺 **EPG program guide** (Now/Next)
- 🔒 **Parental controls** with PIN lock
- 🎨 **Dark/Light themes** — modern responsive UI

## Resource Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| RAM | 48 MB | 128 MB |
| CPU | 0.1 core | 0.5 core |
| Disk | 80 MB | 100 MB |
| Network | 1 Mbps | 10 Mbps |

## Supported Architectures

| Architecture | Tag |
|-------------|-----|
| x86-64 | `amd64` |
| ARM64 | `arm64` |

Multi-arch manifest: `asummoner/tvviewerapp:latest` auto-selects the correct platform.

## Docker Compose

```yaml
services:
  tv-viewer:
    image: asummoner/tvviewerapp:latest
    container_name: tv-viewer
    ports:
      - "8765:8765"
    volumes:
      - tv-viewer-data:/data
    environment:
      - TZ=Asia/Jerusalem
      - SUPABASE_URL=${SUPABASE_URL:-}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY:-}
    deploy:
      resources:
        limits:
          memory: 128M
          cpus: '0.5'
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/api/status')"]
      interval: 60s
      timeout: 5s
      start_period: 30s
      retries: 3

volumes:
  tv-viewer-data:
```

## Data Persistence

Favorites, channel cache, and health data are stored in `/data` inside the container. Mount a volume to preserve data across container upgrades:

```bash
# Named volume (recommended)
docker run -d --name tv-viewer -p 8765:8765 -v tv-viewer-data:/data asummoner/tvviewerapp

# Or bind mount to host directory
docker run -d --name tv-viewer -p 8765:8765 -v /path/to/data:/data asummoner/tvviewerapp
```

**What's persisted in `/data`:**
| File | Purpose |
|------|---------|
| `channels.json` | Channel cache (avoids re-fetching on restart) |
| `favorites.json` | Your saved favorite channels |

## NAS Installation

### Synology (Container Manager)
1. Open **Container Manager** → Registry → Search `asummoner/tvviewerapp`
2. Download `latest` tag
3. Create container: port 8765 → 8765, memory limit 128 MB
4. Start and open `http://synology-ip:8765`

### QNAP (Container Station)
1. Open **Container Station** → Create → Search `asummoner/tvviewerapp`
2. Set port mapping: 8765 → 8765
3. Set memory limit: 128 MB
4. Apply and access via browser

### Unraid
1. Go to **Docker** → Add Container
2. Repository: `asummoner/tvviewerapp`
3. Port: 8765 → 8765
4. Apply

### TrueNAS SCALE
1. Apps → Launch Docker Image
2. Image: `asummoner/tvviewerapp:latest`
3. Port: 8765
4. Save

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TV_VIEWER_WEB_PORT` | `8765` | Server listen port |
| `TZ` | `UTC` | Timezone for EPG schedule |
| `DATA_DIR` | `/data` | Persistent data directory |
| `TELEMETRY_ENABLED` | `true` | Anonymous usage analytics (channel health) |
| `SUPABASE_URL` | _(empty)_ | Supabase project URL for shared analytics |
| `SUPABASE_ANON_KEY` | _(empty)_ | Supabase anon key (public, RLS-protected) |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/status` | Server health + channel count |
| `GET /api/channels?country=US&category=News&limit=50` | Channel list with filters |
| `GET /api/countries` | Available countries |
| `GET /api/categories` | Available categories |
| `GET /api/sources/{channel_name}` | Alternative stream URLs |
| `GET /api/proxy?url=...` | CORS proxy for HLS streams |
| `GET /api/epg/{channel_name}` | EPG program guide |
| `POST /api/health/report` | Report channel status |

## Updating

Your favorites and channel data persist in the `/data` volume across upgrades:

```bash
# Docker Compose (recommended — keeps /data volume intact)
docker compose pull && docker compose up -d

# Manual Docker
docker pull asummoner/tvviewerapp:latest
docker stop tv-viewer && docker rm tv-viewer
docker run -d --name tv-viewer -p 8765:8765 -v tv-viewer-data:/data --restart unless-stopped asummoner/tvviewerapp
```

## Source Code & Documentation

| Resource | Link |
|----------|------|
| 🌐 Homepage | [tv-viewer-app.github.io/tv_viewer](https://tv-viewer-app.github.io/tv_viewer/) |
| 📦 GitHub | [tv-viewer-app/tv_viewer](https://github.com/tv-viewer-app/tv_viewer) |
| 📋 Changelog | [CHANGELOG.md](https://github.com/tv-viewer-app/tv_viewer/blob/master/CHANGELOG.md) |
| 🐛 Issues | [Report a bug](https://github.com/tv-viewer-app/tv_viewer/issues) |

## License

MIT
