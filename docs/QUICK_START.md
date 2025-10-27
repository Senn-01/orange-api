# 🚀 Quick Start Guide - Orange Belgium API

**Get running in 10 minutes!**

---

## Option 1: Docker (Easiest)

### Prerequisites
- Docker & Docker Compose installed
- Orange JSON file

### Steps

```bash
# 1. Navigate to project
cd orange-api

# 2. Start everything (API + PostgreSQL)
docker-compose up -d

# 3. Wait 30 seconds for database to initialize

# 4. Import Orange data
docker-compose exec api python parse_orange_json.py \
  --json /app/orange_full.json \
  --db-url postgresql://orange_user:orange_pass@db:5432/orange_belgium

# 5. Test API
curl http://localhost:8000/health
```

**Done!** API running at http://localhost:8000/docs

---

## Option 2: Local Development

### Prerequisites
- Python 3.10+
- PostgreSQL installed and running

### Steps

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup database
psql -U postgres -c "CREATE DATABASE orange_belgium;"
psql -U postgres -d orange_belgium -f database_schema.sql

# 4. Configure environment
export DATABASE_URL="postgresql://user:pass@localhost/orange_belgium"

# 5. Import data
python parse_orange_json.py \
  --json orange_full.json \
  --db-url $DATABASE_URL

# 6. Run API
uvicorn app.main:app --reload --port 8000
```

**Done!** API running at http://localhost:8000/docs

---

## 🧪 Quick Test

### Test 1: Search Products
```bash
curl "http://localhost:8000/products?group=internet"
```

### Test 2: Calculate Bundle Pricing
```bash
curl -X POST "http://localhost:8000/bundles/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "product_ids": ["54801", "54831"],
    "duration_months": 12
  }'
```

### Test 3: View Active Promotions
```bash
curl "http://localhost:8000/promotions"
```

### Test 4: Interactive Docs
Open in browser: http://localhost:8000/docs

---

## 🤖 Test with Nexus Agent

### System Prompt
```
You have access to the Orange Belgium API at http://localhost:8000

Available endpoints:
- GET /products - Search products
- POST /bundles/calculate - Calculate pricing
- GET /promotions - List active promos

Always use the API for accurate pricing. Never do manual calculations.
```

### Example Agent Query
**User:** "I want fast internet and a mobile plan with lots of data"

**Agent should:**
1. Call `GET /products?group=internet&min_price=50`
2. Call `GET /products?group=mobile`
3. Present options
4. When user decides, call `POST /bundles/calculate` with selection
5. Explain pricing: "First 6 months: €X, then €Y"

---

## 📊 Verify Data Import

```bash
# Check database stats
curl http://localhost:8000/debug/stats

# Expected output:
{
  "products": 15,
  "options": 9,
  "groups": 4,
  "price_rules": 14,
  "promotions": 34
}
```

---

## 🐛 Troubleshooting

### Database Connection Error
```bash
# Check PostgreSQL is running
docker-compose ps  # Docker
# or
pg_isready  # Local

# Verify connection string
echo $DATABASE_URL
```

### Import Failed
```bash
# Check JSON file exists
ls -lh orange_full.json

# Try dry run
python parse_orange_json.py \
  --json orange_full.json \
  --db-url $DATABASE_URL \
  --dry-run
```

### API Not Starting
```bash
# Check logs
docker-compose logs -f api  # Docker
# or check terminal output for errors

# Verify dependencies
pip list | grep fastapi
```

---

## 📱 Production Deployment

**Deploy to Heroku in 5 minutes:**

```bash
# 1. Create app
heroku create orange-api-prod

# 2. Add database
heroku addons:create heroku-postgresql:basic

# 3. Deploy
git push heroku main

# 4. Import data
heroku pg:psql < database_schema.sql
heroku run python parse_orange_json.py \
  --json orange_full.json \
  --db-url $(heroku config:get DATABASE_URL)
```

**See:** `docs/HEROKU_DEPLOYMENT.md` for full guide

---

## 🎯 Next Steps

1. ✅ Verify API is working (`/health` endpoint)
2. ✅ Test pricing calculations (`/bundles/calculate`)
3. ✅ Integrate with your Nexus agent
4. ✅ Deploy to production (Heroku/Docker)
5. ✅ Set up monthly data updates (CRON)

---

## 📞 Support

- **Documentation:** http://localhost:8000/docs
- **Full README:** See `README.md`
- **Deployment:** See `docs/HEROKU_DEPLOYMENT.md`
- **Project Summary:** See `PROJECT_SUMMARY.md`

---

**You're all set!** 🎉

The API is ready to help your Nexus agent guide Orange Belgium customers through subscription choices with precise pricing calculations.
