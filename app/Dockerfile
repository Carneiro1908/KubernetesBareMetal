# Use a slim official Python base image
FROM python:3.11-slim

# Set system-level environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    APP_DIR=/app

# Set workspace directory
WORKDIR ${APP_DIR}

# Install essential system dependencies (for building psycopg2 if necessary)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy python dependencies list and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and frontend static directories
COPY database.py .
COPY server.py .
COPY public/ ./public/

# Expose server port
EXPOSE ${PORT}

# Run the FastAPI server using Uvicorn
CMD ["python", "server.py"]
