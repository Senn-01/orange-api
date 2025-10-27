# Orange Belgium Subscription API

**Production-ready FastAPI for subscription bundle pricing and recommendations.**

Designed to support a Nexus AI agent helping Orange Belgium customers choose and price subscription bundles (Internet + Mobile + TV + options).

---

## 🎯 Features

- **Product Search**: Filter products by group, price, keywords
- **Bundle Validation**: Check if products can be combined
- **Precise Pricing Calculation**: Calculate exact costs with promotions and discounts
- **Month-by-Month Breakdown**: See promotional periods and permanent costs
- **Promotion Management**: View active time-limited offers
- **Token Efficient**: Returns 1-3K tokens vs 48K raw JSON (96% reduction)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Data Ingestion (Monthly CRON)                     │
│  • Parse Orange JSON → PostgreSQL                           │
│  • Normalize products, promotions, price rules              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: FastAPI Endpoints                                 │
│  • GET /products - Search & filter                          │
│  • POST /bundles/calculate - Pricing engine ⭐              │
│  • GET /promotions - Active offers                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Nexus Agent                                       │
│  • Understands user needs                                   │
│  • Queries API with relevant filters                        │
│  • Explains pricing breakdown to customer                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- pip or poetry

### Setup

```bash
# 1. Clone repository
git clone <your-repo>
cd orange-api

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your database credentials

# 5. Setup database
psql -U postgres -c "CREATE DATABASE orange_belgium;"
psql -U postgres -d orange_belgium -f database_schema.sql

# 6. Import Orange data
python parse_orange_json.py \
    --json orange_full.json \
    --db-url "postgresql://user:pass@localhost/orange_belgium"

# 7. Run the API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🚀 Usage

### Example 1: Search for Fast Internet

**Request:**
```bash
curl "http://localhost:8000/products?group=internet&min_price=50"
```

**Response:**
```json
{
  "products": [
    {
      "id": "54801",
      "display_name": "Internet illimité 500 Mbps",
      "monthly_price": 59.00,
      "activation_fee": 39.00,
      "group_name": "Internet"
    },
    {
      "id": "54806",
      "display_name": "Internet illimité 1000 Mbps",
      "monthly_price": 69.00,
      "activation_fee": 39.00,
      "group_name": "Internet"
    }
  ],
  "total_count": 2
}
```

### Example 2: Calculate Bundle Pricing ⭐

**Request:**
```bash
curl -X POST "http://localhost:8000/bundles/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "product_ids": ["54801", "54831"],
    "option_ids": [],
    "duration_months": 12
  }'
```

**Response:**
```json
{
  "products": [
    {
      "id": "54801",
      "display_name": "Internet illimité 500 Mbps",
      "monthly_price": 59.00
    },
    {
      "id": "54831",
      "display_name": "Mobile Medium",
      "monthly_price": 22.00
    }
  ],
  "base_monthly_total": 81.00,
  "permanent_discount_total": 9.00,
  "promotion_discount_total": 15.00,
  
  "applied_price_rules": [
    {
      "name": "Avantage multi-produits",
      "discount_amount": 9.00,
      "duration_months": null
    }
  ],
  
  "applied_promotions": [
    {
      "name": "Promo: -15€ pendant 6 mois",
      "discount_amount": 15.00,
      "duration_months": 6
    }
  ],
  
  "monthly_breakdown": [
    {
      "month": 1,
      "base_price": 81.00,
      "permanent_discounts": 9.00,
      "temporary_discounts": 15.00,
      "total_monthly": 57.00,
      "one_time_fees": 39.00,
      "total_due": 96.00
    },
    {
      "month": 2,
      "total_monthly": 57.00,
      "total_due": 57.00
    },
    ...
    {
      "month": 7,
      "total_monthly": 72.00,
      "total_due": 72.00
    }
  ],
  
  "summary": {
    "first_month_total": 96.00,
    "promotional_period_monthly": 57.00,
    "promotional_period_months": 6,
    "permanent_monthly": 72.00,
    "first_year_total": 825.00,
    "second_year_total": 864.00
  }
}
```

### Example 3: Get Active Promotions

**Request:**
```bash
curl "http://localhost:8000/promotions"
```

**Response:**
```json
{
  "promotions": [
    {
      "id": "55441",
      "name": "Promo : -15€ pendant 12 mois",
      "calculation_value": 15.00,
      "duration_months": 12,
      "start_date": "2025-01-01T00:00:00",
      "end_date": "2025-12-31T23:59:59",
      "legal_summary": "Offre valable du 01/01/2025..."
    }
  ],
  "total_count": 8,
  "as_of_date": "2025-10-27T10:30:00"
}
```

---

## 📊 API Endpoints

| Endpoint | Method | Purpose | Token Cost |
|----------|--------|---------|------------|
| `/products` | GET | Search products | ~500-800 |
| `/products/{id}` | GET | Get product detail | ~200 |
| `/options` | GET | List options | ~300-500 |
| `/bundles/validate` | POST | Check compatibility | ~200 |
| `/bundles/calculate` ⭐ | POST | Calculate pricing | ~1000-1500 |
| `/promotions` | GET | List active promos | ~600-1000 |
| `/groups` | GET | List categories | ~100 |

**Total savings: 94-96% vs raw 48K JSON ✅**

---

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Test specific endpoint
pytest tests/test_bundles.py -v

# With coverage
pytest --cov=app tests/
```

### Manual Testing

```bash
# Health check
curl http://localhost:8000/health

# Interactive docs
open http://localhost:8000/docs
```

---

## 🔄 Updating Data

Orange updates their product catalog monthly. To refresh:

```bash
# 1. Download latest JSON
curl https://www.orange.be/fr/api/obe-dps/v1 > orange_full.json

# 2. Re-import
python parse_orange_json.py \
    --json orange_full.json \
    --db-url $DATABASE_URL

# 3. Verify
curl http://localhost:8000/promotions
```

**Recommended: Set up monthly CRON job**

```cron
# Every 1st of month at 2am
0 2 1 * * /path/to/update_script.sh
```

---

## 🏭 Production Deployment

### Option 1: Heroku

```bash
# Install Heroku CLI
brew install heroku/brew/heroku

# Create app
heroku create orange-api-prod

# Add PostgreSQL
heroku addons:create heroku-postgresql:basic

# Deploy
git push heroku main

# Import data
heroku run python parse_orange_json.py \
    --json orange_full.json \
    --db-url $DATABASE_URL
```

### Option 2: Docker

```bash
# Build
docker build -t orange-api .

# Run
docker run -p 8000:8000 \
    -e DATABASE_URL=postgresql://... \
    orange-api
```

### Option 3: AWS/GCP

See deployment guides in `docs/deployment/`

---

## 📝 Pricing Calculation Logic

### How Discounts Stack

```python
Base Price (€81)
  ↓
- Permanent Discount (€9)  # Avantage multi-produits (ALWAYS)
  ↓
- Promotion (€15)          # Time-limited (6-12 months)
  ↓
= Final Price (€57/month during promo, €72 after)
```

### Key Rules

1. **Permanent discounts** (`price_rules`) always apply
2. **Promotions** are time-limited (6-12 months)
3. **Discounts stack** unless `excludedPromos` conflicts
4. **calculationOrder** determines application order (lower = first)

---

## 🔍 Database Schema

**13 tables:**
- `groups` - Product categories
- `products` - Main subscriptions
- `options` - Add-ons
- `configurators` - Valid bundles
- `price_rules` - Permanent discounts
- `promotions` - Time-limited offers
- `promotion_products` - Links promos to products
- `configurator_products` - Valid product combinations
- *+ junction tables*

**See:** `database_schema.sql` for full details

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

MIT License - See LICENSE file

---

## 🆘 Support

- **Documentation**: `http://localhost:8000/docs`
- **Issues**: GitHub Issues
- **Email**: support@yourcompany.com

---

## ✅ Checklist for Production

- [ ] Environment variables secured
- [ ] Database backups configured
- [ ] Monitoring/logging setup (Sentry, DataDog)
- [ ] Rate limiting implemented
- [ ] Authentication added (if needed)
- [ ] CORS configured properly
- [ ] SSL/HTTPS enabled
- [ ] Health checks working
- [ ] Error alerting configured
- [ ] Monthly data refresh CRON job

---

**Built with ❤️ for Orange Belgium**
