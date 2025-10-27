# Render PostgreSQL Plan Fix

## ✅ Issue Resolved

**Error:** `Legacy Postgres plans, including 'starter', are no longer supported for new databases`

**Root Cause:** Render deprecated their legacy PostgreSQL plans (starter, standard, pro) and introduced new flexible plans with independent compute and storage options.

---

## 🔧 Changes Made

### 1. Updated `render.yaml`

**Before:**
```yaml
databases:
  - name: orange-db
    plan: starter  # ❌ Deprecated
```

**After:**
```yaml
databases:
  - name: orange-db
    plan: basic-1gb  # ✅ New flexible plan
```

### 2. Updated `docs/RENDER_DEPLOYMENT.md`

- Updated manual configuration instructions to use `basic-1gb` plan
- Updated all pricing references to reflect new flexible plans:
  - **basic-1gb:** ~€7/mo (1GB storage)
  - **basic-2gb:** ~€10/mo (2GB storage)  
  - **basic-4gb:** ~€15/mo (4GB storage)
  - **standard-8gb:** ~€25/mo (8GB storage, higher compute)
  - **pro-16gb+:** For production scale

---

## 📊 New Render PostgreSQL Plans

### Flexible Plan Structure

Render's new PostgreSQL plans separate **compute** from **storage**, giving you more flexibility:

| Plan Tier | Example Plans | Starting Price | Use Case |
|-----------|--------------|----------------|----------|
| **Basic** | basic-256mb, basic-512mb, basic-1gb, basic-2gb, basic-4gb | ~$7/mo | Development & small apps |
| **Standard** | standard-8gb, standard-16gb, standard-32gb, standard-64gb | ~$25/mo | Production apps |
| **Pro** | pro-8gb, pro-16gb, pro-32gb, pro-64gb+ | ~$100/mo | High-performance production |

### Key Benefits

1. **Independent Scaling:** Adjust CPU, RAM, and storage separately
2. **More Options:** Wider range of compute configurations
3. **Better Value:** Pay only for what you need
4. **Advanced Features:** Point-in-time recovery on all paid plans

---

## 🚀 Next Steps

### Option 1: Redeploy Using Blueprint (Recommended)

1. **Delete your existing Render services** (if any were partially created)
   - Go to Render Dashboard
   - Delete both `orange-api` and `orange-db` if they exist

2. **Deploy with updated configuration:**
   - Go to Render Dashboard
   - Click **"New +"** → **"Blueprint"**
   - Select your GitHub repo: `Senn-01/orange-api`
   - Branch: `main`
   - Click **"Apply"**

3. **Render will now create:**
   - ✅ Web service with `starter` plan
   - ✅ PostgreSQL database with `basic-1gb` plan
   - ✅ Automatic connection between services

### Option 2: Manual Configuration

If you prefer manual setup:

1. **Create PostgreSQL Database:**
   - Dashboard → "New +" → "PostgreSQL"
   - Name: `orange-db`
   - Database: `orange_belgium`
   - User: `orange_user`
   - Region: Frankfurt
   - **Plan: basic-1gb** ✅
   - Click "Create Database"

2. **Create Web Service:**
   - Dashboard → "New +" → "Web Service"
   - Connect GitHub repo
   - Name: `orange-api`
   - Runtime: Python 3
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Plan: Starter
   - Add environment variable:
     - `DATABASE_URL` → (link to orange-db)
   - Click "Create Web Service"

---

## 💰 Cost Impact

### No Change to Original Estimate

| Component | Plan | Cost |
|-----------|------|------|
| Web Service | Starter | €7/mo |
| PostgreSQL | basic-1gb | ~€7/mo |
| **Total** | | **~€14/mo** |

✅ Same price as before, just updated plan naming

---

## 🔍 Verification

### Check Your Deployment

Once deployed, verify everything works:

```bash
# Test health endpoint
curl https://your-app.onrender.com/health

# Expected response:
{"status": "healthy", "database": "connected"}
```

### Monitor Deployment

- Render Dashboard → Services → orange-api → Events
- Look for:
  - ✅ "Build succeeded"
  - ✅ "Deploy succeeded"
  - ✅ Service status: "Live"

---

## 📚 Additional Resources

- [Render PostgreSQL Flexible Plans](https://render.com/docs/postgresql-refresh)
- [Render Blueprint YAML Reference](https://render.com/docs/blueprint-spec)
- [Render PostgreSQL Pricing](https://render.com/pricing#postgresql)

---

## ✅ Status

**Fixed and Deployed:**
- ✅ `render.yaml` updated with `basic-1gb` plan
- ✅ Documentation updated with new plan names
- ✅ Changes committed and pushed to GitHub
- ✅ Ready for Render deployment

**Commit:** `672602b` - Fix: Update PostgreSQL plan from legacy 'starter' to new 'basic-1gb' plan

---

**You can now proceed with Render deployment!** 🎉

