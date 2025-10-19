# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    cargo \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim 

WORKDIR /app

# Copy installed packages and binaries from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app source
COPY . .

EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
