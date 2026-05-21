# Minimal NAS image (~25MB compressed)
# Supports: Synology, QNAP, Unraid, TrueNAS (amd64 + arm64)

FROM python:3.12-alpine AS builder

WORKDIR /build
COPY web/requirements.txt .
RUN pip install --no-cache-dir --no-compile --prefix=/install -r requirements.txt aiohttp

# ─── Final image ─────────────────────────────────────────────────────────────
FROM python:3.12-alpine

LABEL org.opencontainers.image.title="TV Viewer Web" \
      org.opencontainers.image.description="Lightweight IPTV streaming web interface with 16,000+ live TV channels. Self-hosted, browser-based, NAS-ready." \
      org.opencontainers.image.version="2.13.1" \
      org.opencontainers.image.source="https://github.com/tv-viewer-app/tv_viewer" \
      org.opencontainers.image.url="https://tv-viewer-app.github.io/tv_viewer/" \
      org.opencontainers.image.documentation="https://github.com/tv-viewer-app/tv_viewer/blob/master/DOCKER_README.md" \
      org.opencontainers.image.vendor="TV Viewer App" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.authors="asummoner"

WORKDIR /app

# Copy only pip packages (no build tools in final image)
COPY --from=builder /install /usr/local

# Copy minimal runtime files
COPY config.py .
COPY channels_config.json .
COPY web/ web/
COPY utils/ utils/
COPY core/ core/

# Create persistent data dir and required dirs
RUN mkdir -p /data logs && \
    echo '{"channels":[]}' > /data/channels.json && \
    adduser -S -D tvviewer && \
    chown -R tvviewer /app/logs /data

# Persistent volume for favorites, channels cache, and settings
VOLUME /data

USER tvviewer

ENV TV_VIEWER_WEB_PORT=8765 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data \
    TELEMETRY_ENABLED=true

EXPOSE 8765

HEALTHCHECK --interval=60s --timeout=5s --start-period=15s --retries=2 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8765/api/status')" || exit 1

CMD ["python", "-m", "web.server", "--host", "0.0.0.0", "--port", "8765"]
