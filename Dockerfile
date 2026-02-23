FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (lightweight — uses cloud APIs instead of local ML)
COPY requirements-light.txt .
RUN pip install --no-cache-dir -r requirements-light.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p uploads/web_sessions uploads/line_sessions logs

EXPOSE 5001 5002 5003
