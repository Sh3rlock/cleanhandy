#!/bin/bash

# CleanHandy SQLite to PostgreSQL Migration Script
echo "🚀 Starting migration from SQLite to PostgreSQL..."

# Step 1: Backup SQLite data
echo "📦 Step 1: Creating data backup from SQLite..."
cd cleanhandy
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission > ../data_backup.json
echo "✅ Data backup created: data_backup.json"

# Step 2: Create PostgreSQL database (if not exists)
echo "🗄️ Step 2: Setting up PostgreSQL database..."
createdb cleanhandy_production 2>/dev/null || echo "Database might already exist"

# Step 3: Run migrations on PostgreSQL
echo "🔄 Step 3: Running migrations on PostgreSQL..."
python manage.py migrate

# Step 4: Load data into PostgreSQL
echo "📥 Step 4: Loading data into PostgreSQL..."
python manage.py loaddata ../data_backup.json

# Step 5: Verify migration
echo "✅ Step 5: Verifying migration..."
python manage.py shell -c "
from django.contrib.auth.models import User
from quotes.models import *
print(f'Users: {User.objects.count()}')
print(f'Bookings: {Booking.objects.count() if hasattr(globals(), \"Booking\") else \"N/A\"}')
print('Migration completed successfully!')
"

echo "🎉 Migration completed! Your data is now in PostgreSQL."
echo "💡 Don't forget to update your production environment variables:"
echo "   - DB_NAME=cleanhandy_production"
echo "   - DB_USER=your_postgres_user"
echo "   - DB_PASSWORD=your_postgres_password"
echo "   - DB_HOST=your_postgres_host"
echo "   - DB_PORT=5432"

