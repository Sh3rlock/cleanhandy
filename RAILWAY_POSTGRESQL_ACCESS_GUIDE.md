# Railway PostgreSQL Access Guide

This guide shows you how to access and manage your PostgreSQL database on Railway.

## 🔗 Database Connection Details

Your PostgreSQL database connection details are available in Railway:

### 1. **Get Connection Details from Railway Dashboard**

1. Go to [railway.app](https://railway.app)
2. Select your CleanHandy project
3. Click on your **PostgreSQL service** (not the web app)
4. Go to the **"Variables"** tab
5. You'll see these environment variables:
   - `DATABASE_URL` - Full connection string
   - `PGHOST` - Database host
   - `PGPORT` - Database port (usually 5432)
   - `PGDATABASE` - Database name
   - `PGUSER` - Database username
   - `PGPASSWORD` - Database password

### 2. **Connection String Format**
```
postgresql://username:password@host:port/database_name
```

Example:
```
postgresql://postgres:uNBHWTzTbtZAcmjSSnGoVBbKjBwDbFCo@postgres.railway.internal:5432/railway
```

## 🛠️ Access Methods

### Method 1: Railway CLI (Recommended)

1. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   # or
   curl -fsSL https://railway.app/install.sh | sh
   ```

2. **Login to Railway**:
   ```bash
   railway login
   ```

3. **Connect to your project**:
   ```bash
   railway connect
   ```

4. **Access PostgreSQL shell**:
   ```bash
   railway run psql
   ```

5. **Run SQL commands**:
   ```sql
   -- List all tables
   \dt
   
   -- List all databases
   \l
   
   -- Connect to your database
   \c railway
   
   -- View table structure
   \d quotes_contactinfo
   
   -- Run custom queries
   SELECT * FROM quotes_contactinfo LIMIT 5;
   ```

### Method 2: External Database Client

Use any PostgreSQL client (pgAdmin, DBeaver, TablePlus, etc.):

1. **Host**: `postgres.railway.internal` (or the host from your variables)
2. **Port**: `5432` (or the port from your variables)
3. **Database**: `railway` (or the database name from your variables)
4. **Username**: `postgres` (or the username from your variables)
5. **Password**: The password from your variables

### Method 3: Django Management Commands

1. **Access Railway terminal**:
   - Go to your web service on Railway
   - Click "Deployments" → "View Logs"
   - Look for terminal access option

2. **Run Django database commands**:
   ```bash
   # Check database status
   python manage.py check_db
   
   # Run migrations
   python manage.py migrate
   
   # Create superuser
   python manage.py createsuperuser
   
   # Access Django shell
   python manage.py shell
   ```

## 📊 Database Management Commands

### Using Railway CLI

```bash
# Connect to PostgreSQL
railway run psql

# Run SQL file
railway run psql < backup.sql

# Export database
railway run pg_dump > backup.sql

# Import database
railway run psql < backup.sql
```

### Using Django Shell

```python
# Access Django shell
python manage.py shell

# Example queries
from quotes.models import ContactInfo, Service, Booking

# List all contact info
ContactInfo.objects.all()

# Create new contact info
ContactInfo.objects.create(
    phone="+1-555-0123",
    email="support@thecleanhandy.com",
    address="123 Main St, City, State",
    is_active=True
)

# List all services
Service.objects.all()

# List all bookings
Booking.objects.all()
```

## 🔧 Database Operations

### 1. **Run Migrations**
```bash
# On Railway
railway run python manage.py migrate

# Locally (if you have DATABASE_URL set)
python manage.py migrate
```

### 2. **Create Superuser**
```bash
# On Railway
railway run python manage.py createsuperuser

# Locally
python manage.py createsuperuser
```

### 3. **Load Sample Data**
```bash
# Export from local SQLite
python manage.py dumpdata --natural-foreign --natural-primary > data.json

# Import to Railway PostgreSQL
railway run python manage.py loaddata data.json
```

### 4. **Database Backup**
```bash
# Create backup
railway run pg_dump > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
railway run psql < backup_20241024_130000.sql
```

## 🔍 Troubleshooting

### Common Issues:

1. **"Database does not exist"**
   ```sql
   -- Create database if it doesn't exist
   CREATE DATABASE railway;
   ```

2. **"Permission denied"**
   - Check if you're using the correct credentials
   - Verify the user has proper permissions

3. **"Connection refused"**
   - Check if the PostgreSQL service is running
   - Verify the host and port are correct

4. **"Table does not exist"**
   ```bash
   # Run migrations
   railway run python manage.py migrate
   ```

### Debug Database Connection:

```python
# Test connection in Django shell
python manage.py shell

from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT version();")
print(cursor.fetchone())
```

## 📈 Monitoring

### Check Database Status:
```bash
# Check if database is running
railway run pg_isready

# Check database size
railway run psql -c "SELECT pg_size_pretty(pg_database_size('railway'));"

# Check active connections
railway run psql -c "SELECT count(*) FROM pg_stat_activity;"
```

### View Database Logs:
1. Go to Railway dashboard
2. Click on PostgreSQL service
3. Go to "Deployments" tab
4. Click "View Logs"

## 🔐 Security Notes

- **Never commit database credentials** to version control
- **Use environment variables** for all sensitive data
- **Regular backups** are recommended
- **Monitor database usage** to avoid hitting limits

## 📞 Support

If you encounter issues:
1. Check Railway's documentation: https://docs.railway.app/
2. Check PostgreSQL documentation: https://www.postgresql.org/docs/
3. Check Django database documentation: https://docs.djangoproject.com/en/stable/ref/databases/#postgresql-notes

## 🎯 Quick Start Checklist

- [ ] PostgreSQL service added to Railway project
- [ ] DATABASE_URL environment variable set in web service
- [ ] Migrations run successfully
- [ ] Database accessible via Railway CLI
- [ ] Superuser created
- [ ] Test data loaded (optional)
