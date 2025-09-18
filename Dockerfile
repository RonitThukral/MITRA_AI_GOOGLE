# Use official Python slim image for a lightweight base
FROM python:3.12-slim

# Set working directory in the container
WORKDIR /app

# Install system dependencies (build-essential for compiling packages, if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port (Cloud Run will use this)
EXPOSE 8000

# Run the FastAPI app with Uvicorn
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]