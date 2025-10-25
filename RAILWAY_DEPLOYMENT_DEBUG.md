# Railway Deployment Debug Guide

## 🔍 Current Issue Analysis

The healthcheck is failing because:

1. **Database Connection Issue**: The app is trying to connect to `postgres.railway.internal` which is only accessible from within Railway's network
2. **Startup Process**: The app can't start because it can't connect to the database
3. **Healthcheck Failure**: Since the app doesn't start, the healthcheck fails

## 🚀 Solutions

### Solution 1: Use Railway's External Database URL

1. **Get External Database URL**:
   - Go to Railway Dashboard
   - Click on your PostgreSQL service
   - Go to "Connect" tab (not Variables)
   - Look for "Public Networking" section
   - Copy the external connection string (should look like: `postgresql://postgres:password@containers-us-west-123.railway.app:5432/railway`)

2. **Update Environment Variable**:
   - Go to your web service
   - Click "Variables" tab
   - Update `DATABASE_URL` with the external URL

### Solution 2: Use Railway CLI to Access Database

```bash
# Install Railway CLI (alternative methods)
npx @railway/cli login
npx @railway/cli connect

# Access database
npx @railway/cli run psql

# Run migrations
npx @railway/cli run python manage.py migrate
```

### Solution 3: Deploy and Debug on Railway

1. **Deploy your current changes**:
   ```bash
   git add .
   git commit -m "Fix Railway deployment configuration"
   git push
   ```

2. **Check Railway logs**:
   - Go to your web service
   - Click "Deployments" → "View Logs"
   - Look for error messages

3. **Access Railway terminal**:
   - Look for terminal access in the logs
   - Run: `python manage.py test_db_connection`

## 🔧 Configuration Changes Made

### 1. **Updated railway.json**
- Changed builder to `DOCKERFILE`
- Removed problematic `startCommand`
- Increased healthcheck timeout to 10 minutes

### 2. **Updated Dockerfile**
- Removed migrations from build process
- Added robust startup script
- Better error handling

### 3. **Created docker_start.sh**
- Waits for database connection (up to 3 minutes)
- Runs migrations with error handling
- Starts Gunicorn with proper configuration

## 📋 Next Steps

1. **Get External Database URL** from Railway dashboard
2. **Update DATABASE_URL** environment variable
3. **Deploy changes** and monitor logs
4. **Test database connection** via Railway terminal

## 🔍 Debugging Commands

### Check Database Connection:
```bash
# On Railway terminal
python manage.py test_db_connection --show-credentials
```

### Check App Status:
```bash
# On Railway terminal
python manage.py check
```

### Run Migrations:
```bash
# On Railway terminal
python manage.py migrate
```

## 🚨 Common Issues

1. **"Connection refused"**: Database URL is incorrect or database is not running
2. **"Host not found"**: Using internal hostname instead of external
3. **"Permission denied"**: Database credentials are incorrect
4. **"Table does not exist"**: Migrations haven't been run

## 📞 Support

If issues persist:
1. Check Railway's documentation: https://docs.railway.app/
2. Check Railway's status page: https://status.railway.app/
3. Review your Railway project logs
4. Contact Railway support if needed
