# VolatiQ - Quantitative Risk Intelligence Platform
# Multi-stage Docker build for optimized production deployment

# Build stage for Python dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r volatiq && useradd -r -g volatiq volatiq

# Copy Python packages from builder stage
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/data /app/model/saved_model \
    && chown -R volatiq:volatiq /app

# Make sure scripts are executable
RUN chmod +x /app/scripts/start.sh || true

# Switch to non-root user
USER volatiq

# Add local Python packages to PATH
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

# Expose ports for API and Dashboard
EXPOSE 5000 8050

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Default command (can be overridden)
CMD ["python", "api/app.py"]
