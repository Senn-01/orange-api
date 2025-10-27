# Monthly Data Refresh Setup

**Automatic monthly updates of Orange Belgium product catalog and promotions.**

---

## 🎯 Overview

The refresh system:
1. ✅ Runs automatically on the 1st of every month at 2 AM
2. ✅ Fetches latest Orange JSON
3. ✅ Validates data structure
4. ✅ Backs up current database
5. ✅ Imports new data
6. ✅ Runs smoke tests
7. ✅ Restores backup if anything fails
8. ✅ Sends Slack notification (optional)

**Completely automated, safe, and pragmatic.** 🚀

---

## 📋 Setup Instructions

### Step 1: Configure GitHub Secrets

In your GitHub repository:

1. Go to **Settings** > **Secrets and variables** > **Actions**
2. Click **New repository secret**
3. Add these secrets:

| Secret Name | Value | Required |
|-------------|-------|----------|
| `DATABASE_URL` | Your PostgreSQL connection string | ✅ Yes |
| `API_URL` | Your deployed API URL | ✅ Yes |
| `SLACK_WEBHOOK` | Slack webhook for alerts | ⬜ Optional |

**Example values:**
```bash
DATABASE_URL=postgresql://user:pass@your-db-host.com:5432/orange_belgium
API_URL=https://your-app.herokuapp.com
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Step 2: Commit the Workflow

The workflow file is already created at:
```
.github/workflows/refresh_data.yml
```

Just commit and push:
```bash
git add .github/workflows/refresh_data.yml
git add refresh_orange_data.py
git commit -m "Add monthly data refresh automation"
git push
```

### Step 3: Verify Setup

**Test manually:**
1. Go to GitHub **Actions** tab
2. Click **Monthly Data Refresh**
3. Click **Run workflow** > **Run workflow**
4. Watch the logs

**Expected output:**
```
🚀 Starting Orange data refresh pipeline
📡 Fetching data from Orange API...
✅ Fetched 142567 bytes
🔍 Validating JSON structure...
✅ Validation passed: 15 products, 34 promotions
💾 Creating database backup...
✅ Backup created: /tmp/backup_20251027_020000.sql
📥 Importing data to database...
✅ Imported 15 products
✅ Imported 34 promotions
🧪 Running smoke tests...
✅ Smoke tests passed
✅ Refresh completed successfully!
```

---

## 📅 Schedule

**Default:** 1st of every month at 2:00 AM (UTC)

**To change schedule:**

Edit `.github/workflows/refresh_data.yml`:

```yaml
on:
  schedule:
    # Format: minute hour day month day-of-week
    - cron: '0 2 1 * *'  # 2 AM on 1st of month
```

**Common schedules:**
```yaml
'0 2 1 * *'   # Monthly: 1st at 2 AM
'0 2 1,15 * *' # Twice monthly: 1st and 15th at 2 AM
'0 2 * * 1'   # Weekly: Every Monday at 2 AM
'0 2 * * *'   # Daily: Every day at 2 AM
```

Use [crontab.guru](https://crontab.guru) to help with cron syntax.

---

## 🔔 Notifications

### Slack Alerts (Optional)

**Setup:**
1. Create Slack incoming webhook:
   - Go to Slack > Apps > Incoming Webhooks
   - Add to your workspace
   - Copy webhook URL
   
2. Add to GitHub secrets:
   ```
   SLACK_WEBHOOK=https://hooks.slack.com/services/...
   ```

3. You'll receive notifications:
   - ✅ On successful refresh
   - 🚨 On failure (with error details)

**Without Slack:**
- Check GitHub Actions logs for results
- GitHub will email you on workflow failure

---

## 🛡️ Safety Features

### 1. Validation Before Import

The script validates:
- ✅ JSON has required sections (products, promotions, etc.)
- ✅ Minimum product count (≥10)
- ✅ Product structure unchanged (has _id, name, price, etc.)

**If validation fails:**
- ❌ Import is aborted
- 🔔 Alert sent
- 📋 Manual review required

### 2. Database Backup

Before importing new data:
- 💾 Full database backup created
- 📏 Backup size validated
- 📁 Stored temporarily

**If import fails:**
- 🔄 Automatic rollback from backup
- 🔔 Alert sent
- ✅ API continues working with old data

### 3. Smoke Tests

After import, tests verify:
- ✅ Can query products
- ✅ Can query promotions
- ✅ Bundle validation works

**If smoke tests fail:**
- 🔄 Automatic rollback
- 🔔 Alert sent

---

## 🐛 Troubleshooting

### Workflow Failed

**Check the logs:**
1. Go to **Actions** tab
2. Click the failed run
3. Expand steps to see error

**Common issues:**

| Error | Cause | Solution |
|-------|-------|----------|
| `DATABASE_URL not set` | Secret not configured | Add DATABASE_URL secret |
| `Failed to fetch Orange data` | Orange API down | Wait and retry manually |
| `Validation failed` | Orange changed JSON | Manual review required |
| `Backup failed` | Database permissions | Check pg_dump is available |

### Manually Trigger Refresh

```bash
# Option 1: Via GitHub UI
# Actions > Monthly Data Refresh > Run workflow

# Option 2: Via API
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
  https://api.github.com/repos/YOUR_ORG/YOUR_REPO/actions/workflows/refresh_data.yml/dispatches \
  -d '{"ref":"main"}'
```

### Restore from Backup Manually

If you need to restore manually:

```bash
# 1. Download backup (if saved)
# Backups are in /tmp/ on the runner (ephemeral)
# For production, modify script to upload to S3/GCS

# 2. Restore locally
psql $DATABASE_URL < backup.sql

# 3. Verify
curl https://your-api.com/health
```

---

## 📊 Monitoring

### View Past Runs

1. Go to **Actions** tab
2. See all past refresh runs
3. Check success rate

### Metrics to Watch

- **Success rate:** Should be 100% (or close)
- **Duration:** Typically 2-5 minutes
- **Product count:** Should remain stable (~15)
- **Promotion count:** Will vary (5-40)

### Alerts to Act On

🚨 **CRITICAL** - Act immediately:
- "Restore failed" - Database may be corrupted
- "Validation failed" - Orange changed structure

⚠️ **WARNING** - Review soon:
- "Backup failed" - Next import is risky
- "Product count low" - Data might be incomplete

ℹ️ **INFO** - For your awareness:
- "Promotion count low" - Normal variation
- "Smoke tests passed" - All good!

---

## 🔄 Manual Refresh

**If you need to refresh outside the schedule:**

```bash
# Option 1: Via GitHub Actions (easiest)
# Actions > Monthly Data Refresh > Run workflow

# Option 2: Run locally
export DATABASE_URL="postgresql://..."
python refresh_orange_data.py

# Option 3: In Docker
docker-compose exec api python refresh_orange_data.py
```

---

## 🏗️ Architecture

```
GitHub Actions Runner
  ↓
  1. Fetch Orange JSON
  ↓
  2. Validate structure
  ↓
  3. Backup database (pg_dump)
  ↓
  4. Import new data (parse_orange_json.py)
  ↓
  5. Run smoke tests
  ↓
  6. If fail: Restore backup (psql)
  ↓
  7. Send notification (Slack)
```

**Why GitHub Actions?**
- ✅ Free for public repos
- ✅ $0.008/min for private repos (≈$0.04/month)
- ✅ No infrastructure to manage
- ✅ Built-in logging and notifications
- ✅ Easy to modify/test

**Alternatives:**
- Heroku Scheduler (€25/month)
- System CRON (requires server)
- AWS CloudWatch Events (pay per invocation)

---

## 📝 Customization

### Change Validation Rules

Edit `refresh_orange_data.py`:

```python
# Adjust thresholds
MIN_PRODUCTS = 10  # Expect at least 10 products
MIN_PROMOTIONS = 5  # Expect at least 5 promotions

# Add more checks
def validate_json_structure(data):
    # Your custom validation here
    if data['products'][0]['price']['monthlyPrice'] < 0:
        return False
    return True
```

### Add More Tests

Edit `refresh_orange_data.py`:

```python
def run_smoke_tests():
    # Add test: Check a known bundle still works
    calculation = calculate_bundle(['54801', '54831'])
    if calculation.base_monthly_total != Decimal('81.00'):
        log("Known bundle price changed!")
        return False
    
    return True
```

### Upload Backups to Cloud

```python
def backup_database():
    # ... create backup ...
    
    # Upload to S3
    s3_client.upload_file(
        backup_path,
        'my-backups',
        f'orange-db-{datetime.now()}.sql'
    )
```

---

## ✅ Success Criteria

Your refresh automation is working well when:

- ✅ Runs automatically every month
- ✅ No manual intervention required
- ✅ Completes in under 5 minutes
- ✅ Sends notification on completion
- ✅ API continues working after refresh
- ✅ Can rollback if problems detected

---

## 🎯 Next Steps

1. ✅ Commit the workflow files
2. ✅ Configure GitHub secrets
3. ✅ Test manually once
4. ✅ Set up Slack notifications (optional)
5. ✅ Monitor first scheduled run
6. ✅ Document any Orange-specific quirks you discover

---

**You're all set!** The system will automatically keep your API data fresh. 🎉

**Questions?** Check the main README or the script comments.
