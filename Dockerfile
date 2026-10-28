FROM python:3.9-slim

WORKDIR /app

# Install system dependencies:
# - gcc, default-libmysqlclient-dev, pkg-config: required to compile mysqlclient
# - curl: required for Docker healthcheck and deployment validation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker build cache
COPY requirements.txt requirement.txt ./

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code
COPY . .

# Expose the application port
EXPOSE 5000

# Docker healthcheck
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "app.py"]
