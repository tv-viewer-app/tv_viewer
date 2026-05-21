# TV Viewer Web 📺

[![GitHub Release](https://img.shields.io/github/v/release/tv-viewer-app/tv_viewer)](https://github.com/tv-viewer-app/tv_viewer/releases/latest)
[![Docker Image Size](https://img.shields.io/docker/image-size/asummoner/tvviewerapp/latest)](https://hub.docker.com/r/asummoner/tvviewerapp)
[![Docker Pulls](https://img.shields.io/docker/pulls/asummoner/tvviewerapp)](https://hub.docker.com/r/asummoner/tvviewerapp)

**Lightweight IPTV streaming web interface with 16,000+ channels. Perfect for NAS devices.**

## Quick Start

```bash
docker run -d --name tv-viewer -p 8765:8765 --restart unless-stopped asummoner/tvviewerapp
```

Open **http://your-nas-ip:8765** in any browser.

## Features

- 🌍 16,000+ live TV channels from 55+ countries
- 🎬 In-browser HLS playback (no VLC needed)
- 🔀 Automatic source switching on stream failure
- 📡 CORS proxy — plays streams that normally block browsers
- 🗺️ Interactive country map for channel discovery
- ❤️ Favorites with server-side persistence
- 📊 Health tracking — filters broken channels automatically
- 📺 EPG program guide (Now/Next)
- 🔒 Parental controls with PIN lock

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
| ARMv7 | `arm/v7` |

Multi-arch manifest: `asummoner/tvviewerapp:latest` auto-selects the correct platform.

## Docker Compose

```yaml
services:
  tv-viewer:
    image: asummoner/tvviewerapp:latest
    container_name: tv-viewer
    ports:
      - "8765:8765"
    environment:
      - TZ=Asia/Jerusalem
    deploy:
      resources:
        limits:
          memory: 128M
          cpus: '0.5'
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8765/api/status')"]
      interval: 60s
      timeout: 5s
      retries: 2
```

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

```bash
docker pull asummoner/tvviewerapp:latest
docker stop tv-viewer && docker rm tv-viewer
docker run -d --name tv-viewer -p 8765:8765 --restart unless-stopped asummoner/tvviewerapp
```

## Source Code

[GitHub: tv-viewer-app/tv_viewer](https://github.com/tv-viewer-app/tv_viewer)

## License

MIT
