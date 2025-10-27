# Render Deployment Guide

**Deploy Orange Belgium API to Render in 15 minutes**

---

## Why Render?

- **Cheaper:** €7/month vs Heroku's €25/month
- **Simpler:** Auto-deploy from GitHub
- **Free Tier:** Available for testing (Heroku removed theirs)
- **Modern:** Better UI, faster deployments
- **PostgreSQL included:** Database + backup built-in

**Cost comparison:**
- Render Starter: €14/month (API + DB)
- Heroku Basic: €34/month (API + DB)
- **Savings: 58%**

---

## Prerequisites

- GitHub account
- Render account (render.com)
- Project pushed to GitHub repository

---

## Deployment Method 1: Blueprint (Automatic) ✅ RECOMMENDED

**Uses the `render.yaml` file we created**

### Step 1: Push to GitHub

```bash
cd orange-api
git init
git add .
git commit -m "Initial commit: Orange API"

# Create repo on GitHub, then:
git remote add origin https://github.com/yourname/orange-api.git
git push -u origin main
```

### Step 2: Connect to Render

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub account
4. Select repository: `yourname/orange-api`
5. Branch: `main`
6. Click **"Apply"**

**Render will automatically:**
- Create web service (FastAPI)
- Create PostgreSQL database
- Link them together
- Deploy your code
- Set environment variables

### Step 3: Wait for Deployment

**Duration: ~5 minutes**

Monitor progress:
- Dashboard → Services → orange-api → Events

**Success indicators:**
- ✅ "Build succeeded"
- ✅ "Deploy succeeded"
- ✅ Service status: "Live"

### Step 4: Get Your API URL

```
https://orange-api-XXXXX.onrender.com
```

Test it:
```bash
curl https://orange-api-XXXXX.onrender.com/health
```

### Step 5: Initialize Database

**Option A: Shell access**
```bash
# In Render dashboard:
# Services → orange-api → Shell tab

# Run schema
cat database_schema.sql | psql $DATABASE_URL

# Import data
python parse_orange_json.py \
  --json orange_full.json \
  --db-url $DATABASE_URL
```

**Option B: Local connection**
```bash
# Get database connection string
# Dashboard → Databases → orange-db → Connect → External Connection

# Copy PSQL Command and run locally
psql postgresql://user:pass@host/db < database_schema.sql

# Upload JSON and import (see below)
```

---

## Deployment Method 2: Manual Configuration

If you prefer manual setup or need custom configuration:

### Step 1: Create Web Service

1. Dashboard → **"New +"** → **"Web Service"**
2. Connect GitHub repo
3. Configure:
   - **Name:** orange-api
   - **Region:** Frankfurt (or nearest)
   - **Branch:** main
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Starter ($7/mo)

4. Click **"Create Web Service"**

### Step 2: Create PostgreSQL Database

1. Dashboard → **"New +"** → **"PostgreSQL"**
2. Configure:
   - **Name:** orange-db
   - **Database:** orange_belgium
   - **User:** orange_user
   - **Region:** Frankfurt (same as web service)
   - **Plan:** Starter ($7/mo)

3. Click **"Create Database"**

### Step 3: Connect Services

1. Go to web service: orange-api → Environment
2. Add environment variable:
   - **Key:** `DATABASE_URL`
   - **Value:** Select "orange-db" from dropdown
   - This automatically uses internal connection string

3. Add more variables:
   - `ENVIRONMENT` = `production`
   - `PYTHON_VERSION` = `3.11.0`

4. Click **"Save Changes"** (triggers redeploy)

---

## Database Setup

### Import Schema

**Method 1: Render Shell**
```bash
# Dashboard → orange-api → Shell

# Download schema
curl https://raw.githubusercontent.com/yourname/orange-api/main/database_schema.sql -o schema.sql

# Import
psql $DATABASE_URL < schema.sql
```

**Method 2: External Connection**
```bash
# Get connection details
# Dashboard → orange-db → Connect → External Connection

# Import locally
psql "postgresql://user:pass@host:5432/db" < database_schema.sql
```

### Import Orange Data

**Upload JSON to service:**

```bash
# Method 1: Via Shell (if small file)
# Dashboard → orange-api → Shell
# Paste file contents or wget from URL

# Method 2: Add to repo (recommended)
git add orange_full.json
git commit -m "Add Orange data"
git push

# Then in Shell:
python parse_orange_json.py \
  --json orange_full.json \
  --db-url $DATABASE_URL
```

**Verify import:**
```bash
# In Shell or via curl
curl https://your-api.onrender.com/debug/stats
```

---

## Configuration Files

### Procfile (Optional for Render)

Render doesn't require Procfile, but you can add one:

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### .renderignore (Optional)

Exclude files from deployment:

```
tests/
*.pyc
__pycache__/
.env
.git/
.vscode/
*.md
```

---

## Custom Domain

### Step 1: Add Domain

1. Dashboard → orange-api → Settings → Custom Domains
2. Click **"Add Custom Domain"**
3. Enter: `api.yourcompany.com`

### Step 2: Configure DNS

Add CNAME record in your DNS provider:

```
Type:  CNAME
Name:  api
Value: orange-api-XXXXX.onrender.com
TTL:   300
```

### Step 3: Wait for SSL

**Duration: ~5 minutes**

Render automatically provisions SSL certificate (Let's Encrypt)

**Verify:**
```bash
curl https://api.yourcompany.com/health
```

---

## Environment Variables

### Required Variables

Already set via render.yaml or manual config:

| Variable | Value | Source |
|----------|-------|--------|
| `DATABASE_URL` | Auto-populated | From database connection |
| `ENVIRONMENT` | production | Manual |
| `PORT` | Auto-set | Render system |

### Optional Variables

Add in Dashboard → Environment:

```bash
# CORS origins (if restricting)
CORS_ORIGINS=https://yourapp.com,https://api.yourcompany.com

# Logging level
LOG_LEVEL=INFO

# If adding authentication
JWT_SECRET_KEY=your-secret-key-here
```

---

## Monitoring & Logs

### View Logs

**Real-time:**
```
Dashboard → orange-api → Logs tab
```

**Download:**
```
Dashboard → orange-api → Logs → Download
```

### Health Monitoring

Render automatically monitors `/health` endpoint

**Configure:**
Dashboard → orange-api → Settings → Health Check Path

### Metrics

**View:**
- Dashboard → orange-api → Metrics tab
- CPU usage
- Memory usage
- Request count
- Response times

### Alerts (Paid plans only)

Set up notifications:
- Dashboard → Account → Notifications
- Configure Slack/Email/Webhook

---

## Scheduled Tasks (Data Updates)

### Option 1: Render Cron Jobs

**Create cron job:**

1. Dashboard → **"New +"** → **"Cron Job"**
2. Configure:
   - **Name:** orange-data-update
   - **Command:** `python scripts/update_data.py`
   - **Schedule:** `0 2 * * *` (Daily at 2 AM)
   - **Region:** Frankfurt
   - **Plan:** Free (included)

3. Create `scripts/update_data.py`:

```python
#!/usr/bin/env python3
"""
Monthly data update script for Orange API
Fetches latest JSON and imports to database
"""
import requests
import subprocess
import os

def main():
    # Download latest Orange JSON
    url = "https://www.orange.be/fr/api/obe-dps/v1"
    response = requests.get(url)
    
    with open('/tmp/orange_full.json', 'w') as f:
        f.write(response.text)
    
    # Import to database
    db_url = os.getenv('DATABASE_URL')
    subprocess.run([
        'python', 'parse_orange_json.py',
        '--json', '/tmp/orange_full.json',
        '--db-url', db_url
    ])
    
    print("✅ Data update complete")

if __name__ == '__main__':
    main()
```

### Option 2: GitHub Actions

**Create `.github/workflows/update-data.yml`:**

```yaml
name: Update Orange Data

on:
  schedule:
    - cron: '0 2 1 * *'  # 1st of every month at 2 AM
  workflow_dispatch:  # Manual trigger

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install requests psycopg2-binary
      
      - name: Download Orange JSON
        run: curl https://www.orange.be/fr/api/obe-dps/v1 > orange_full.json
      
      - name: Import to database
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: python parse_orange_json.py --json orange_full.json --db-url $DATABASE_URL
```

**Setup:**
1. GitHub repo → Settings → Secrets → Actions
2. Add secret: `DATABASE_URL` (get from Render dashboard)

---

## Backup & Restore

### Automatic Backups

**Enabled by default on Render:**
- Daily backups (last 7 days)
- Weekly backups (last 4 weeks)
- Monthly backups (last 3 months)

**Access:**
Dashboard → orange-db → Backups tab

### Manual Backup

```bash
# Get connection string
# Dashboard → orange-db → Connect → External Connection

# Backup
pg_dump "postgresql://user:pass@host:5432/db" > backup.sql

# Or with compression
pg_dump "postgresql://user:pass@host:5432/db" | gzip > backup.sql.gz
```

### Restore from Backup

```bash
# Restore from SQL file
psql "postgresql://user:pass@host:5432/db" < backup.sql

# Or from Render dashboard
# Dashboard → orange-db → Backups → Restore
```

---

## Scaling

### Vertical Scaling (More Resources)

**Upgrade web service:**
1. Dashboard → orange-api → Settings → Plan
2. Options:
   - **Starter:** €7/mo (512 MB RAM)
   - **Standard:** €21/mo (2 GB RAM) ✅ Production
   - **Pro:** €85/mo (8 GB RAM)

**Upgrade database:**
1. Dashboard → orange-db → Settings → Plan
2. Options:
   - **Starter:** €7/mo (1 GB storage)
   - **Standard:** €21/mo (10 GB storage)
   - **Pro:** €90/mo (100 GB storage)

### Horizontal Scaling (Multiple Instances)

**Add more instances:**
1. Dashboard → orange-api → Settings → Scaling
2. Set instances: 2-10
3. Load balancing: Automatic

**Cost:** €7/mo per additional instance

---

## CI/CD Pipeline

### Auto-Deploy on Push

**Already configured via render.yaml:**
- Push to `main` branch → Auto-deploy
- Pull requests → Preview environments (paid plans)

### Manual Deploy

```bash
# Dashboard → orange-api → Manual Deploy
# Or via API:
curl -X POST https://api.render.com/v1/services/YOUR_SERVICE_ID/deploys \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Deploy Hooks

**Get webhook URL:**
Dashboard → orange-api → Settings → Deploy Hook

**Use in CI:**
```bash
curl -X POST https://api.render.com/deploy/srv-XXXXX?key=XXXXX
```

---

## Troubleshooting

### Build Fails

**Check logs:**
Dashboard → orange-api → Events → Build logs

**Common issues:**
- Missing dependencies → Check `requirements.txt`
- Python version mismatch → Add `runtime.txt` with `python-3.11.0`
- Build timeout → Optimize dependencies

### Database Connection Error

```bash
# Verify DATABASE_URL is set
# Dashboard → orange-api → Environment

# Test connection in Shell
psql $DATABASE_URL -c "SELECT version();"
```

### Service Won't Start

**Check start command:**
Dashboard → orange-api → Settings → Start Command

**Should be:**
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Slow Performance

**Check metrics:**
Dashboard → orange-api → Metrics

**Solutions:**
- Upgrade plan (more RAM/CPU)
- Add database indexes
- Enable connection pooling
- Add Redis cache (separate service)

### API Returns 503

**Causes:**
- Service is deploying (wait 2-3 minutes)
- Service crashed (check logs)
- Health check failing (verify `/health` endpoint)

---

## Cost Optimization

### Development Setup (€14/month)
```
Web Service: Starter (€7)
Database: Starter (€7)
Total: €14/month
```

### Production Setup (€42/month)
```
Web Service: Standard (€21)
Database: Standard (€21)
Total: €42/month
```

### High-Traffic Setup (€175/month)
```
Web Service: Pro (€85)
Database: Pro (€90)
Total: €175/month
```

### Free Tier (Testing Only)
```
Web Service: Free (suspended after 15 min inactivity)
Database: Free (90 days trial, then paid)
```

---

## Security Checklist

- ✅ Environment variables (no secrets in code)
- ✅ SSL/HTTPS (automatic)
- ✅ Database backups (automatic)
- ✅ IP allowlist for database (configure if needed)
- [ ] Add rate limiting (implement in code or use Cloudflare)
- [ ] Add authentication (JWT tokens recommended)
- [ ] Configure CORS properly (whitelist specific domains)
- [ ] Enable DDoS protection (Cloudflare proxy)
- [ ] Monitor logs for suspicious activity

---

## Migration from Heroku

### Export Heroku Database

```bash
# Create backup
heroku pg:backups:capture -a your-heroku-app

# Download
heroku pg:backups:download -a your-heroku-app

# Import to Render
psql "postgresql://user:pass@host:5432/db" < latest.dump
```

### Update Environment Variables

```bash
# Get from Heroku
heroku config -a your-heroku-app

# Set in Render
# Dashboard → orange-api → Environment
```

### Switch DNS

1. Test Render deployment
2. Update DNS to point to Render
3. Monitor for 24 hours
4. Decommission Heroku app

---

## Render vs Heroku Comparison

| Feature | Render | Heroku |
|---------|--------|--------|
| **Starter Plan** | €7/mo | ❌ Removed |
| **Standard Plan** | €21/mo | €25/mo |
| **Free Tier** | ✅ Yes | ❌ Removed |
| **Auto-Deploy** | ✅ GitHub | ✅ Git push |
| **SSL** | ✅ Free | ✅ Free |
| **Backups** | ✅ Included | ✅ Paid plans |
| **Preview Envs** | ✅ Paid | ✅ Paid |
| **PostgreSQL** | ✅ Included | ✅ Addon |
| **Logs** | 7 days | 1500 lines |
| **Custom Domains** | ✅ Unlimited | ✅ Unlimited |
| **Build Time** | ~3 min | ~2 min |
| **Cold Start** | ~1 sec | ~1 sec |

---

## Getting Help

**Render Support:**
- Documentation: https://render.com/docs
- Community: https://community.render.com
- Support: support@render.com (paid plans)
- Status: https://status.render.com

**API Issues:**
- Check logs first
- Verify environment variables
- Test locally with Docker
- Review deployment events

---

## Quick Reference

### Deploy Command
```bash
git push origin main  # Auto-deploys
```

### View Logs
```bash
# Dashboard → orange-api → Logs
# Or install Render CLI:
render logs orange-api
```

### Database Access
```bash
# Get connection string from dashboard
psql "postgresql://user:pass@host:5432/db"
```

### Redeploy
```bash
# Dashboard → orange-api → Manual Deploy
# Or commit and push to trigger auto-deploy
```

---

## Next Steps

1. ✅ Deploy to Render (auto or manual method)
2. ✅ Initialize database (schema + data import)
3. ✅ Test endpoints (`/health`, `/products`, `/bundles/calculate`)
4. ✅ Configure custom domain (optional)
5. ✅ Set up scheduled data updates (cron job)
6. ✅ Configure monitoring & alerts
7. ✅ Integrate with Nexus agent
8. ✅ Monitor performance & costs

---

**Deployment complete!** 🚀

Your API is live at: `https://orange-api-XXXXX.onrender.com/docs`

Access OpenAPI spec: `https://orange-api-XXXXX.onrender.com/openapi.yaml`
