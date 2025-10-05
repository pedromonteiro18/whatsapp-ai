# Multi-stage Dockerfile for WhatsApp AI Chatbot
# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=whatsapp_ai_chatbot.settings

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder and install
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache /wheels/* && \
    rm -rf /wheels

# Create non-root user
RUN groupadd -r django && \
    useradd -r -g django -d /app -s /sbin/nologin django && \
    mkdir -p /app/logs /app/static /app/media && \
    chown -R django:django /app

# Copy project files
COPY --chown=django:django . /app/

# Create gunicorn configuration
RUN echo 'import multiprocessing\n\
\n\
# Server socket\n\
bind = "0.0.0.0:8000"\n\
backlog = 2048\n\
\n\
# Worker processes\n\
workers = multiprocessing.cpu_count() * 2 + 1\n\
worker_class = "sync"\n\
worker_connections = 1000\n\
max_requests = 1000\n\
max_requests_jitter = 100\n\
timeout = 30\n\
keepalive = 2\n\
\n\
# Logging\n\
accesslog = "-"\n\
errorlog = "-"\n\
loglevel = "info"\n\
access_log_format = "%%(h)s %%(l)s %%(u)s %%(t)s \\"%%(r)s\\" %%(s)s %%(b)s \\"%%(f)s\\" \\"%%(a)s\\" %%(D)s"\n\
\n\
# Process naming\n\
proc_name = "whatsapp_ai_chatbot"\n\
\n\
# Server mechanics\n\
daemon = False\n\
pidfile = None\n\
user = None\n\
group = None\n\
tmp_upload_dir = None\n\
\n\
# SSL (uncomment for HTTPS)\n\
# keyfile = "/path/to/keyfile"\n\
# certfile = "/path/to/certfile"\n\
\n\
# Graceful shutdown\n\
graceful_timeout = 30\n\
' > /app/gunicorn.conf.py

# Make entrypoint executable
COPY --chown=django:django docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Switch to non-root user
USER django

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/').read()" || exit 1

# Set entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command
CMD ["gunicorn", "whatsapp_ai_chatbot.wsgi:application", "--config", "/app/gunicorn.conf.py"]
