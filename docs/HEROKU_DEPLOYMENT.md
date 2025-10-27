# Heroku Deployment Guide

## Prerequisites

- Heroku CLI installed: `brew install heroku/brew/heroku`
- Git repository initialized
- Heroku account created

---

## Step 1: Create Heroku App

```bash
# Login to Heroku
heroku login

# Create new app
heroku create orange-api-prod

# Or with specific region
heroku create orange-api-prod --region eu
```

---

## Step 2: Add PostgreSQL Database

```bash
# Add Heroku Postgres (Basic tier: €9/month)
heroku addons:create heroku-postgresql:basic

# Or Essential tier for production (€50/month)
heroku addons:create heroku-postgresql:essential-0

# Verify database
heroku pg:info
```

---

## Step 3: Configure Environment Variables

```bash
# Set environment
heroku config:set ENVIRONMENT=production

# Database URL is automatically set by Heroku
# Verify:
heroku config
```

---

## Step 4: Create Procfile

Create `Procfile` in project root:

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

## Step 5: Deploy

```bash
# Add Heroku remote (if not already added)
heroku git:remote -a orange-api-prod

# Deploy
git push heroku main

# Or from a different branch:
git push heroku your-branch:main
```

---

## Step 6: Initialize Database

```bash
# Run schema
heroku pg:psql < database_schema.sql

# Or via psql:
heroku pg:psql -c "$(cat database_schema.sql)"
```

---

## Step 7: Import Orange Data

```bash
# Option A: Import from local JSON
heroku run python parse_orange_json.py \
    --json orange_full.json \
    --db-url $(heroku config:get DATABASE_URL)

# Option B: Copy JSON to Heroku first
heroku ps:copy orange_full.json
heroku run python parse_orange_json.py \
    --json orange_full.json \
    --db-url $(heroku config:get DATABASE_URL)
```

---

## Step 8: Scale Dynos

```bash
# Scale to 1 web dyno (free tier)
heroku ps:scale web=1

# For production (hobby: €7/month)
heroku ps:type hobby

# Or professional (€25-250/month)
heroku ps:type professional-1x
```

---

## Step 9: Configure Domain (Optional)

```bash
# Add custom domain
heroku domains:add api.yourcompany.com

# Get DNS target
heroku domains

# Add DNS record in your DNS provider:
# Type: CNAME
# Name: api
# Value: <heroku-dns-target>
```

---

## Step 10: Enable SSL

```bash
# SSL is automatic on Heroku
# Verify:
curl https://your-app.herokuapp.com/health
```

---

## Monitoring & Logs

```bash
# View logs
heroku logs --tail

# View metrics
heroku pg:info
heroku pg:diagnose

# Install logging add-on (optional)
heroku addons:create papertrail:choklad
```

---

## Scheduled Data Updates

### Option A: Heroku Scheduler (€25/month)

```bash
# Add scheduler
heroku addons:create scheduler:standard

# Open scheduler dashboard
heroku addons:open scheduler

# Add job:
# Frequency: Daily at 2:00 AM
# Command: python update_orange_data.py
```

### Option B: External CRON

Use external service (GitHub Actions, cron-job.org) to trigger:

```bash
# Create update endpoint in API
POST /admin/update-data

# Call from external CRON
curl -X POST https://your-app.herokuapp.com/admin/update-data \
  -H "Authorization: Bearer YOUR_SECRET_TOKEN"
```

---

## Backup Strategy

```bash
# Manual backup
heroku pg:backups:capture

# Schedule automatic backups (included in paid plans)
heroku pg:backups:schedule DATABASE_URL --at '02:00 Europe/Brussels'

# Download backup
heroku pg:backups:download

# Restore from backup
heroku pg:backups:restore b001 DATABASE_URL
```

---

## Rollback

```bash
# View releases
heroku releases

# Rollback to previous version
heroku rollback v123
```

---

## Cost Estimation

### Minimal Setup (Development)
- App: Free (or Hobby €7/month)
- Database: Basic €9/month
- **Total: €9-16/month**

### Production Setup
- App: Professional €25/month
- Database: Essential €50/month
- Scheduler: €25/month
- Total: **€100/month**

---

## Troubleshooting

### Database Connection Errors

```bash
# Check connection
heroku pg:psql
# Should connect successfully

# Check DATABASE_URL
heroku config:get DATABASE_URL
```

### App Crashes

```bash
# Check logs
heroku logs --tail --source app

# Restart
heroku restart

# Check dyno status
heroku ps
```

### Import Failures

```bash
# Check if file exists
heroku run ls -la

# Run with verbose logging
heroku run python parse_orange_json.py --json orange_full.json --db-url $(heroku config:get DATABASE_URL) -v
```

---

## Security Checklist

- [ ] Environment variables configured (no secrets in code)
- [ ] SSL enabled (automatic on Heroku)
- [ ] Database access restricted (Heroku internal only)
- [ ] CORS configured for your domain only
- [ ] Rate limiting implemented (if needed)
- [ ] Authentication added for admin endpoints
- [ ] Regular backups scheduled
- [ ] Monitoring/alerting configured

---

## Alternative: Deploy to Railway.app

Railway is simpler and cheaper for small projects:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway up

# Add PostgreSQL
railway add postgresql

# Set environment
railway variables set ENVIRONMENT=production
```

Cost: €5-20/month (pay-as-you-go)

---

**Deployment complete!** 🚀

Access your API at: `https://your-app.herokuapp.com/docs`
