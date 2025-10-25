# Use a lightweight Python base image
FROM python:3.11-slim

# Install system dependencies needed by WeasyPrint and others
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libpango-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libcairo2 \
    libpangocairo-1.0-0 \
    fonts-liberation \
    shared-mime-info \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Collect static files (migrations will run at runtime)
RUN python manage.py collectstatic --noinput

# Expose the default port (optional, doesn't affect Railway)
EXPOSE 8000

# Make startup script executable
RUN chmod +x docker_start.sh

# Start the application
CMD ["./docker_start.sh"]
