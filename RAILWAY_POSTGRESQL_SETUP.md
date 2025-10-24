# Railway PostgreSQL Setup Guide

This guide will help you connect your Django CleanHandy website to PostgreSQL on Railway.

## Prerequisites

- Railway account
- Your Django project already deployed on Railway
- Local development environment set up

## Step 1: Add PostgreSQL Service to Railway

1. **Go to your Railway project dashboard**
   - Visit [railway.app](https://railway.app)
   - Select your CleanHandy project

2. **Add PostgreSQL service**
   - Click the "+" button to add a new service
   - Select "Database" → "PostgreSQL"
   - Railway will automatically provision a PostgreSQL database

3. **Get the DATABASE_URL**
   - Once PostgreSQL is provisioned, click on the PostgreSQL service
   - Go to the "Variables" tab
   - Copy the `DATABASE_URL` value (it will look like: `postgresql://postgres:password@host:port/database`)

## Step 2: Configure Environment Variables

1. **Add DATABASE_URL to your web service**
   - Go to your web service (the one running your Django app)
   - Click on "Variables" tab
   - Add a new variable:
     - **Name**: `DATABASE_URL`
     - **Value**: The DATABASE_URL you copied from the PostgreSQL service

2. **Optional: Add other database-related variables**
   - `DB_ENGINE`: `django.db.backends.postgresql`
   - `DB_NAME`: Your database name
   - `DB_USER`: Your database user
   - `DB_PASSWORD`: Your database password
   - `DB_HOST`: Your database host
   - `DB_PORT`: Your database port (usually 5432)

## Step 3: Update Your Django Settings

Your `settings.py` has already been updated to automatically detect and use PostgreSQL when `DATABASE_URL` is present:

```python
# Check if we're on Railway with PostgreSQL
if os.getenv('DATABASE_URL'):
    # Railway PostgreSQL configuration
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(os.getenv('DATABASE_URL'))
    }
else:
    # Local SQLite configuration
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
```

## Step 4: Install Dependencies

Your `requirements.txt` has been updated with the necessary PostgreSQL packages:

```
psycopg2-binary==2.9.9
dj-database-url==2.1.0
```

## Step 5: Deploy and Run Migrations

1. **Deploy your changes**
   - Commit and push your changes to your repository
   - Railway will automatically redeploy your application

2. **Run migrations on Railway**
   - Go to your web service on Railway
   - Click on "Deployments" tab
   - Click on the latest deployment
   - Click "View Logs" to see the deployment process

3. **Run migrations manually (if needed)**
   - Go to your web service
   - Click on "Deployments" → "View Logs"
   - In the terminal, run:
     ```bash
     python manage.py migrate
     ```

## Step 6: Migrate Data from SQLite (Optional)

If you have existing data in your SQLite database that you want to migrate to PostgreSQL:

1. **Export data from SQLite**
   ```bash
   python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission > data.json
   ```

2. **Import data to PostgreSQL**
   - After your PostgreSQL setup is complete and migrations are run
   - Run: `python manage.py loaddata data.json`

## Step 7: Verify the Setup

1. **Check your application logs**
   - Go to your web service → Deployments → View Logs
   - Look for any database connection errors

2. **Test database operations**
   - Visit your website
   - Try creating a user account or booking
   - Check if data is being saved to PostgreSQL

## Troubleshooting

### Common Issues:

1. **"psycopg2 not found" error**
   - Make sure `psycopg2-binary==2.9.9` is in your requirements.txt
   - Redeploy your application

2. **"dj_database_url not found" error**
   - Make sure `dj-database-url==2.1.0` is in your requirements.txt
   - Redeploy your application

3. **Database connection refused**
   - Check that `DATABASE_URL` is correctly set in your environment variables
   - Verify the PostgreSQL service is running on Railway

4. **Migration errors**
   - Make sure all your migrations are up to date
   - Run `python manage.py migrate` manually

### Railway-Specific Tips:

- Railway provides a free PostgreSQL database with limited storage
- For production, consider upgrading to a paid plan for better performance
- Monitor your database usage in the Railway dashboard
- Use Railway's built-in database management tools for debugging

## Environment Variables Summary

Add these to your Railway web service:

```
DATABASE_URL=postgresql://postgres:password@host:port/database
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=cleanhandy-production.up.railway.app,thecleanhandy.com
```

## Next Steps

1. Test your application thoroughly
2. Set up database backups (Railway provides automatic backups on paid plans)
3. Monitor database performance
4. Consider setting up database connection pooling for better performance

## Support

If you encounter issues:
1. Check Railway's documentation: https://docs.railway.app/
2. Check Django's PostgreSQL documentation: https://docs.djangoproject.com/en/stable/ref/databases/#postgresql-notes
3. Review your application logs in Railway dashboard
