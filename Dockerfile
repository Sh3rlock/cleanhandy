# Use a lightweight Python base image
FROM python:3.11-slim

# Install system dependencies needed by WeasyPrint and others
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libpango-1.0-0 \
    libgdk-pixbuf2.0-0 \
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

# (Optional) Static + Migrations (if handled at build)
# RUN python manage.py collectstatic --noinput
# RUN python manage.py migrate

# Expose the port for the app
EXPOSE 8000

# Start the application with Gunicorn
CMD ["gunicorn", "cleanhandy.wsgi:application", "--bind", "0.0.0.0:8000"]
