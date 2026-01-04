# Multi-stage build for Nodes application

# =============================================================================
# Stage 1: Build frontend
# =============================================================================
FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files first for better layer caching
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm ci --silent

# Copy source files
COPY frontend/ ./

# Build the frontend for production
RUN npm run build

# =============================================================================
# Stage 2: Python backend with built frontend
# =============================================================================
FROM python:3.14-slim

WORKDIR /app

# Install system dependencies needed for some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend source code
COPY backend/ ./backend/

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create data directory for SQLite database
RUN mkdir -p /app/data && chmod 755 /app/data

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    NODES_DATABASE_PATH=/app/data/nodes.db \
    NODES_HOST=0.0.0.0 \
    NODES_PORT=8000

# Expose port
EXPOSE 8000

# Set working directory to backend for running the app
WORKDIR /app/backend

# Health check using curl (more reliable than Python in container)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
CMD ["python", "-m", "app.main"]
