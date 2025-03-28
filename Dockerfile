# Use a Python image with system-level control
FROM python:3.11-slim

# Install system dependencies (for WeasyPrint, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpango-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libcairo2 \
    libpangocairo-1.0-0 \
    libgobject-2.0-0 \
    fonts-liberation \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Collect static files and run migrations (optional if needed at build)
# RUN python manage.py collectstatic --noinput
# RUN python manage.py migrate

# Expose port
EXPOSE 8000

# Start Gunicorn
CMD ["gunicorn", "quotes.wsgi:application", "--bind", "0.0.0.0:8000"]
