FROM python:3.12-slim

WORKDIR /app

# Install only web server dependencies
RUN pip install --no-cache-dir fastapi uvicorn[standard] aiohttp defusedxml certifi

# Copy only what the web server needs
COPY config.py .
COPY channels.json .
COPY channels_config.json .
COPY web/ web/
COPY utils/ utils/
COPY core/ core/

# Create required directories
RUN mkdir -p logs

# Default port
ENV TV_VIEWER_WEB_PORT=8765

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=3s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8765/api/status')" || exit 1

CMD ["python", "-m", "web.server", "--host", "0.0.0.0", "--port", "8765"]
