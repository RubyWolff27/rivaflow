# RivaFlow Deployment Guide - Render

Complete guide to deploying RivaFlow on Render with PostgreSQL database and automatic deployments from GitHub.

## Overview

This deployment will set up:
- **Web Service**: FastAPI backend + React frontend (served together)
- **PostgreSQL Database**: Managed by Render (free tier)
- **Automatic Deployments**: Auto-deploy on git push to main branch
- **HTTPS**: Automatic SSL certificates

**Estimated deployment time**: 15-20 minutes
**Cost**: $0 (Free tier for both web service and database)

---

## Prerequisites

- [x] GitHub account with RivaFlow repository
- [x] Render account (sign up with GitHub at https://render.com)
- [x] Code changes committed and pushed to GitHub

---

## Part 1: Push Code Changes to GitHub

The codebase has been updated with Render-specific configurations. Push these changes:

```bash
# Check git status
git status

# Add all changes
git add .

# Commit changes
git commit -m "Add Render deployment configuration with PostgreSQL support"

# Push to GitHub
git push origin main
```

---

## Part 2: Create PostgreSQL Database on Render

### 1. Log into Render Dashboard

1. Go to https://dashboard.render.com
2. Sign in with your GitHub account

### 2. Create New PostgreSQL Database

1. Click **"New +"** button in the top right
2. Select **"PostgreSQL"**

### 3. Configure Database

Fill in the following settings:

- **Name**: `rivaflow-db`
- **Database**: `rivaflow` (default is fine)
- **User**: `rivaflow` (default is fine)
- **Region**: Choose closest to you (e.g., Oregon, Ohio, Frankfurt)
- **PostgreSQL Version**: 16 (latest)
- **Plan**: **Free** (select the free tier)

### 4. Create Database

1. Click **"Create Database"**
2. Wait 1-2 minutes for provisioning
3. **IMPORTANT**: Keep this tab open - you'll need the database URL

### 5. Get Internal Database URL

Once created, on the database page:

1. Scroll down to **"Connections"** section
2. Find **"Internal Database URL"**
3. It looks like: `postgresql://rivaflow:xxxxx@dpg-xxxxx/rivaflow`
4. **Copy this URL** - you'll need it in the next step

---

## Part 3: Create Web Service on Render

### 1. Create New Web Service

1. In Render Dashboard, click **"New +"** → **"Web Service"**
2. Connect to your GitHub repository

### 2. Connect GitHub Repository

1. If first time: Click **"Connect account"** and authorize Render to access GitHub
2. Find **"RubyWolff27/rivaflow"** repository
3. Click **"Connect"**

### 3. Configure Web Service

Fill in the settings:

**Basic Settings:**
- **Name**: `rivaflow` (or choose your own - this will be your URL)
- **Region**: Same as your database (e.g., Oregon)
- **Branch**: `main`
- **Root Directory**: Leave empty
- **Runtime**: **Python 3**
- **Build Command**:
  ```bash
  pip install -r rivaflow/requirements.txt && cd web && npm install && npm run build && cd ..
  ```
- **Start Command**:
  ```bash
  python -c "from rivaflow.db.database import init_db; init_db()" && uvicorn rivaflow.api.main:app --host 0.0.0.0 --port $PORT
  ```

**Instance Type:**
- Select **Free** tier

### 4. Add Environment Variables

Scroll down to **"Environment Variables"** section and add these:

#### Required Variables:

1. **DATABASE_URL** (from Part 2, step 5)
   - Key: `DATABASE_URL`
   - Value: `postgresql://rivaflow:xxxxx@dpg-xxxxx/rivaflow` (your Internal Database URL)

2. **SECRET_KEY** (generate a secure key)
   - Key: `SECRET_KEY`
   - Value: Generate with this command on your local machine:
     ```bash
     python -c "import secrets; print(secrets.token_urlsafe(32))"
     ```
   - Copy the output and paste it here

3. **ALLOWED_ORIGINS** (your Render app URL)
   - Key: `ALLOWED_ORIGINS`
   - Value: `https://rivaflow.onrender.com` (replace `rivaflow` with your chosen name from step 3)
   - If you chose a different name, use `https://YOUR-APP-NAME.onrender.com`

4. **PYTHON_VERSION**
   - Key: `PYTHON_VERSION`
   - Value: `3.11.0`

### 5. Create Web Service

1. Click **"Create Web Service"** at the bottom
2. Render will start building and deploying your app
3. This takes **10-15 minutes** on first deployment (installing dependencies, building frontend, running migrations)

---

## Part 4: Monitor Deployment

### Watch Build Logs

1. You'll see the build logs in real-time
2. Look for these stages:
   - ✅ Installing Python dependencies
   - ✅ Installing Node.js dependencies
   - ✅ Building frontend (npm run build)
   - ✅ Running database migrations
   - ✅ Starting FastAPI server

### Expected Build Output

```
Installing Python dependencies...
Installing Node.js dependencies...
> rivaflow-web@0.1.0 build
> tsc && vite build
✓ built in 15.23s
[DB] Applying migration: 001_initial_schema.sql
[DB] Successfully applied migration: 001_initial_schema.sql
...
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Deployment Complete

When you see:
```
==> Your service is live 🎉
```

Your app is deployed!

---

## Part 5: Access Your Application

### Get Your URL

Your app will be available at:
```
https://YOUR-APP-NAME.onrender.com
```

For example: `https://rivaflow.onrender.com`

### Test Your Deployment

1. Open your Render URL in a browser
2. You should see the RivaFlow login/register page
3. Create a new account
4. Test logging in
5. Try creating a training session

### Share with Friends

Give your friends the URL:
```
https://YOUR-APP-NAME.onrender.com
```

They can:
1. Click **"Register"** to create an account
2. Fill in their email, password, first name, last name
3. Start logging their training sessions!

---

## Part 6: Automatic Deployments

### How It Works

Render automatically watches your `main` branch on GitHub:

1. You make code changes locally
2. Commit and push to GitHub: `git push origin main`
3. Render detects the push
4. Automatically rebuilds and redeploys your app
5. Takes 3-5 minutes for subsequent deployments

### Disable Auto-Deploy (Optional)

If you want manual deployments:

1. Go to your web service in Render Dashboard
2. Click **"Settings"** tab
3. Scroll to **"Build & Deploy"**
4. Toggle off **"Auto-Deploy"**
5. Now you'll need to click **"Manual Deploy"** → **"Deploy latest commit"**

---

## Part 7: Common Issues & Troubleshooting

### Issue: Build Fails with "ModuleNotFoundError"

**Fix**: Make sure all dependencies are in `rivaflow/requirements.txt`

### Issue: "DATABASE_URL not set" Error

**Fix**: Check environment variables in Render dashboard:
1. Go to your web service
2. Click **"Environment"** tab
3. Verify `DATABASE_URL` is set correctly
4. If missing, add it and redeploy

### Issue: CORS Errors in Browser Console

**Fix**: Update `ALLOWED_ORIGINS` environment variable:
1. Go to your web service settings
2. Update `ALLOWED_ORIGINS` to include your actual Render URL
3. Format: `https://YOUR-APP-NAME.onrender.com` (no trailing slash)
4. Save and redeploy

### Issue: "Frontend not built" Error

**Fix**: Check build logs for frontend build errors:
1. Go to your web service in Render
2. Click **"Logs"** tab
3. Look for errors during `npm run build`
4. Fix TypeScript errors or missing dependencies
5. Commit and push to trigger rebuild

### Issue: App Sleeps After Inactivity (Free Tier)

**Expected Behavior**: Render's free tier spins down after 15 minutes of inactivity
- First request after sleep takes 30-60 seconds to wake up
- Subsequent requests are fast
- **Upgrade to paid tier ($7/month) for always-on service**

### Issue: Database Connection Errors

**Fix**: Verify database is running:
1. Go to your PostgreSQL database in Render
2. Check status is "Available"
3. Verify `DATABASE_URL` in web service matches database Internal URL
4. Check database logs for errors

---

## Part 8: Monitoring & Maintenance

### View Logs

**Application Logs:**
1. Go to your web service in Render
2. Click **"Logs"** tab
3. See real-time application logs

**Database Logs:**
1. Go to your PostgreSQL database
2. Click **"Logs"** tab
3. Monitor database activity

### View Metrics

1. Go to your web service
2. Click **"Metrics"** tab
3. See:
   - CPU usage
   - Memory usage
   - Request rates
   - Response times

### Backup Database (Recommended)

Free tier databases are not automatically backed up. To backup manually:

1. Go to your PostgreSQL database in Render
2. Click **"Connect"** button to get connection details
3. Use `pg_dump` from your local machine:
   ```bash
   pg_dump postgresql://rivaflow:xxxxx@dpg-xxxxx/rivaflow > rivaflow_backup.sql
   ```

Or install a backup service from the Render marketplace.

---

## Part 9: Upgrading to Paid Tier (Optional)

### Free Tier Limitations

- **Web Service**: Spins down after 15 minutes of inactivity
- **Database**: 90-day expiration, no backups
- **Build Minutes**: 400 minutes/month

### Paid Plans

**Starter ($7/month per service)**
- Web service: Always-on, no spin down
- Database: Persistent, automatic backups
- Better performance

**To Upgrade:**
1. Go to your service in Render
2. Click **"Settings"** → **"Instance Type"**
3. Select **"Starter"**
4. Add payment method
5. Upgrade

---

## Part 10: Next Steps

### ✅ You're Live!

Your RivaFlow app is now deployed and accessible to anyone with the URL.

### Share Your App

1. Post your URL on social media
2. Invite your training partners
3. Share in BJJ communities

### Customize Your Domain (Optional)

Render allows custom domains (requires paid plan):

1. Buy a domain (e.g., from Namecheap, Google Domains)
2. In Render, go to your web service → **"Settings"** → **"Custom Domains"**
3. Follow instructions to point your domain to Render
4. Render automatically provisions SSL certificate

Example: `rivaflow.com` instead of `rivaflow.onrender.com`

### Monitor Usage

- Check Render dashboard regularly
- Monitor user signups
- Review logs for errors
- Consider upgrading if you hit free tier limits

---

## Support & Resources

### Render Documentation
- https://render.com/docs

### RivaFlow Issues
- https://github.com/RubyWolff27/rivaflow/issues

### Need Help?
- Check Render's community forum
- Review application logs in Render dashboard
- Check database connectivity

---

## Summary Checklist

- [ ] Pushed code changes to GitHub
- [ ] Created PostgreSQL database on Render
- [ ] Copied Internal Database URL
- [ ] Created web service on Render
- [ ] Added environment variables (DATABASE_URL, SECRET_KEY, ALLOWED_ORIGINS, PYTHON_VERSION)
- [ ] Waited for first deployment (10-15 min)
- [ ] Tested app at Render URL
- [ ] Created test account
- [ ] Shared URL with friends

**Congratulations! RivaFlow is now live on the web!** 🥋🎉
