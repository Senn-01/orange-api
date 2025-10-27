# 🗂️ Orange Belgium API - Codebase Structure

**Quick Reference Guide - What's Where and Why**

---

## 📁 Complete Directory Tree

```
orange-api/
│
├── 📂 app/                          # Main application code
│   ├── __init__.py                  # Python package marker
│   ├── main.py                      # ⭐ FastAPI app + endpoints (300 lines)
│   ├── models.py                    # 📋 Pydantic models (350 lines)
│   ├── database.py                  # 🗄️ Database queries (480 lines)
│   └── calculator.py                # 🧮 Pricing engine (520 lines)
│
├── 📂 tests/                        # Test suite
│   ├── __init__.py                  # Python package marker
│   └── test_calculator.py           # 🧪 Unit tests (450 lines)
│
├── 📂 docs/                         # Documentation
│   ├── RENDER_DEPLOYMENT.md         # 🚀 Render deployment guide
│   └── HEROKU_DEPLOYMENT.md         # 🚀 Heroku deployment guide
│
├── 📄 database_schema.sql           # 🗄️ PostgreSQL schema (450 lines)
├── 📄 parse_orange_json.py          # 📥 JSON import script (430 lines)
│
├── 📄 requirements.txt              # 📦 Python dependencies
├── 📄 .env.example                  # 🔧 Environment variables template
│
├── 📄 Dockerfile                    # 🐳 Container image
├── 📄 docker-compose.yml            # 🐳 Local dev environment
├── 📄 render.yaml                   # ☁️ Render deployment config
│
├── 📄 README.md                     # 📖 Main documentation
├── 📄 QUICK_START.md                # ⚡ Quick setup guide
├── 📄 PROJECT_SUMMARY.md            # 📊 Complete overview
├── 📄 orange_api_analysis.md        # 🔍 JSON structure analysis
│
└── 📄 orange_full.json              # 📋 Orange data (48K tokens)

```

---

## 🎯 File Categories

### **Category 1: Core Application (Must Understand)**

These are the files that make the API work:

```
app/
├── main.py         ← START HERE: API endpoints
├── models.py       ← Data structures & validation
├── calculator.py   ← Pricing logic (the brain)
└── database.py     ← Database operations
```

### **Category 2: Setup & Configuration**

These files set up your environment:

```
database_schema.sql    ← Database tables
parse_orange_json.py   ← Data import
requirements.txt       ← Dependencies
.env.example          ← Configuration template
docker-compose.yml    ← Local dev setup
```

### **Category 3: Deployment**

Choose one based on your hosting:

```
render.yaml                    ← For Render.com
docs/RENDER_DEPLOYMENT.md     ← Render guide
docs/HEROKU_DEPLOYMENT.md     ← Heroku guide
Dockerfile                    ← For custom hosting
```

### **Category 4: Documentation**

Reference materials:

```
README.md              ← Full documentation
QUICK_START.md        ← Get running fast
PROJECT_SUMMARY.md    ← Technical overview
orange_api_analysis.md ← JSON analysis
```

---

## 📖 Detailed File Guide

### **🔴 Critical Files (Must Read First)**

#### 1. `app/main.py` (300 lines)
**What:** The FastAPI application with all HTTP endpoints  
**Why:** This is your API's "front door"  
**Contains:**
- 8 API endpoints (products, bundles, promotions, etc.)
- Request/response handling
- Error handling
- Health checks
- OpenAPI YAML endpoint (NEW!)

**Key endpoints:**
```python
GET  /products              # Search products
POST /bundles/calculate     # Calculate pricing ⭐ MAIN ONE
GET  /promotions            # List active promos
GET  /openapi.yaml          # Download API spec
```

**When to edit:** Adding new endpoints or changing API behavior

---

#### 2. `app/calculator.py` (520 lines)
**What:** The pricing calculation engine (the brain!)  
**Why:** Does all the complex math so the LLM doesn't have to  
**Contains:**
- `RuleEvaluator` - Checks if promotions apply
- `DiscountCalculator` - Computes discount amounts
- `PricingCalculator` - Orchestrates everything

**Example flow:**
```python
Base Price (€81)
  ↓
- Permanent Discounts (€9)   # Applied here
  ↓
- Promotions (€15)            # Applied here
  ↓
= Final Price (€57)           # Result
```

**When to edit:** Changing pricing logic or discount rules

---

#### 3. `app/models.py` (350 lines)
**What:** Pydantic models (data structures)  
**Why:** Type safety & automatic validation  
**Contains:**
- `ProductDetail` - Product information
- `BundleCalculation` - Pricing response
- `PromotionBase` - Promotion details
- Request/response models for all endpoints

**Example:**
```python
class BundleCalculation(BaseModel):
    products: List[ProductDetail]
    base_monthly_total: Decimal
    monthly_breakdown: List[MonthlyBreakdown]
    summary: PricingSummary
```

**When to edit:** Adding new fields or changing data structures

---

#### 4. `app/database.py` (480 lines)
**What:** All database queries  
**Why:** Separates data access from business logic  
**Contains:**
- `get_products()` - Search products
- `get_price_rules()` - Permanent discounts
- `get_active_promotions()` - Time-limited offers
- Connection management

**When to edit:** Adding new queries or changing database operations

---

### **🟡 Setup Files (Use Once)**

#### 5. `database_schema.sql` (450 lines)
**What:** PostgreSQL database structure  
**Why:** Defines all tables, indexes, and relationships  
**Contains:**
- 13 tables (products, promotions, price_rules, etc.)
- Indexes for fast queries
- Foreign keys & constraints
- Helper functions

**Usage:**
```bash
psql -d orange_belgium -f database_schema.sql
```

**When to edit:** Changing database structure (rare)

---

#### 6. `parse_orange_json.py` (430 lines)
**What:** Imports Orange JSON into database  
**Why:** Converts 48K JSON → structured tables  
**Contains:**
- JSON parser
- Data normalization
- Relationship mapping
- Import statistics

**Usage:**
```bash
python parse_orange_json.py \
  --json orange_full.json \
  --db-url postgresql://...
```

**When to edit:** Never (unless JSON structure changes)

---

#### 7. `requirements.txt`
**What:** Python package dependencies  
**Why:** Ensures consistent versions  
**Contains:**
```
fastapi==0.104.1
uvicorn==0.24.0
psycopg2-binary==2.9.9
pydantic==2.5.0
pyyaml==6.0.1  # NEW! For OpenAPI YAML
```

**Usage:**
```bash
pip install -r requirements.txt
```

---

#### 8. `docker-compose.yml`
**What:** Local development environment  
**Why:** Run API + PostgreSQL with one command  
**Contains:**
- API service configuration
- PostgreSQL service
- Automatic networking

**Usage:**
```bash
docker-compose up -d
```

**When to use:** Local development

---

### **🟢 Deployment Files (Choose One)**

#### 9. `render.yaml` (NEW!)
**What:** Render.com deployment configuration  
**Why:** Auto-deploy with one click  
**Contains:**
- Web service config (API)
- Database config (PostgreSQL)
- Environment variables
- Health checks

**Cost:** €14/month (cheaper than Heroku!)

---

#### 10. `Dockerfile`
**What:** Docker container image  
**Why:** Consistent deployment anywhere  
**Usage:**
```bash
docker build -t orange-api .
docker run -p 8000:8000 orange-api
```

---

### **📘 Documentation Files**

#### 11. `README.md`
**What:** Main documentation (400 lines)  
**Contains:**
- Architecture overview
- API usage examples
- Integration guide
- Deployment instructions

**Start here for:** Understanding the project

---

#### 12. `QUICK_START.md` (NEW!)
**What:** Get running in 10 minutes  
**Contains:**
- Docker setup (3 commands)
- Local setup (6 steps)
- Quick tests

**Start here for:** Getting it running fast

---

#### 13. `PROJECT_SUMMARY.md` (NEW!)
**What:** Complete technical overview  
**Contains:**
- Implementation statistics
- Design decisions
- Testing checklist
- Production readiness

**Use for:** Understanding technical details

---

#### 14. `docs/RENDER_DEPLOYMENT.md` (NEW!)
**What:** Complete Render deployment guide  
**Contains:**
- Step-by-step instructions
- Blueprint vs manual methods
- Troubleshooting
- Cost comparison

**Use when:** Deploying to Render.com

---

## 🔄 How Files Work Together

### **Request Flow:**

```
1. HTTP Request arrives
   ↓
2. app/main.py (endpoint receives request)
   ↓
3. app/models.py (validates request data)
   ↓
4. app/database.py (fetches data from PostgreSQL)
   ↓
5. app/calculator.py (calculates pricing)
   ↓
6. app/models.py (formats response)
   ↓
7. app/main.py (returns JSON response)
```

### **Data Flow:**

```
orange_full.json (48K tokens)
   ↓
parse_orange_json.py (parses & normalizes)
   ↓
PostgreSQL database (structured tables)
   ↓
app/database.py (queries database)
   ↓
app/calculator.py (processes data)
   ↓
API response (1-3K tokens)
```

### **Deployment Flow:**

```
Local Development:
  docker-compose.yml → Docker → API running

Production (Render):
  render.yaml → Render platform → API deployed
  
Production (Heroku):
  Procfile → Heroku platform → API deployed
```

---

## 🎓 Learning Path

### **Day 1: Understand the API**
1. Read `QUICK_START.md` (get it running)
2. Open `http://localhost:8000/docs` (interactive docs)
3. Skim `app/main.py` (see the endpoints)
4. Test `/products` and `/bundles/calculate`

### **Day 2: Understand the Pricing Logic**
1. Read `orange_api_analysis.md` (understand data structure)
2. Study `app/calculator.py` (pricing engine)
3. Look at `tests/test_calculator.py` (see examples)
4. Trace a calculation manually

### **Day 3: Deployment**
1. Choose platform (Render or Heroku)
2. Read deployment guide
3. Follow step-by-step
4. Test production API

---

## 🔍 Quick Finder

**Looking for...?**

| I want to... | File to check |
|-------------|---------------|
| Add a new endpoint | `app/main.py` |
| Change pricing logic | `app/calculator.py` |
| Add a field to response | `app/models.py` |
| Change database query | `app/database.py` |
| Update database schema | `database_schema.sql` |
| Deploy to Render | `render.yaml` + `docs/RENDER_DEPLOYMENT.md` |
| Deploy to Heroku | `docs/HEROKU_DEPLOYMENT.md` |
| Run locally | `docker-compose.yml` |
| Install dependencies | `requirements.txt` |
| Test the code | `tests/test_calculator.py` |
| Understand the data | `orange_api_analysis.md` |
| Get started quickly | `QUICK_START.md` |

---

## 📊 Files by Size

```
Largest (Most Complex):
  1. app/calculator.py        (520 lines) ← Pricing engine
  2. app/database.py          (480 lines) ← Database queries
  3. database_schema.sql      (450 lines) ← Database structure
  4. tests/test_calculator.py (450 lines) ← Tests
  5. parse_orange_json.py     (430 lines) ← JSON parser

Medium:
  6. app/models.py            (350 lines) ← Data models
  7. app/main.py              (300 lines) ← API endpoints

Documentation:
  8. PROJECT_SUMMARY.md       (500+ lines)
  9. README.md                (400+ lines)
  10. docs/RENDER_DEPLOYMENT.md (400+ lines)

Small:
  - requirements.txt          (20 lines)
  - docker-compose.yml        (50 lines)
  - render.yaml               (50 lines)
  - Dockerfile                (30 lines)
```

---

## 🎨 Visual Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  USER / NEXUS AGENT                                         │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓ HTTP Request
┌─────────────────────────────────────────────────────────────┐
│  app/main.py                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  /products   │  │  /bundles/   │  │ /promotions  │     │
│  │              │  │  calculate   │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓ Uses
┌─────────────────────────────────────────────────────────────┐
│  app/models.py                                               │
│  (Validates request/response with Pydantic)                  │
└─────────────────┬───────────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        ↓                   ↓
┌──────────────┐    ┌──────────────────┐
│ app/         │    │ app/calculator.py│
│ database.py  │    │ (Pricing Engine) │
│ (SQL Queries)│    │                  │
└──────┬───────┘    └──────────────────┘
       │
       ↓
┌─────────────────────────────────────────────────────────────┐
│  PostgreSQL Database                                         │
│  (Created from database_schema.sql)                          │
│  (Populated by parse_orange_json.py)                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Which Files Do You Actually Need to Touch?

### **For Normal Use:**
- ✅ `.env` (configure database connection)
- ✅ `orange_full.json` (update monthly)
- ✅ That's it!

### **For Customization:**
- `app/main.py` - Add endpoints
- `app/calculator.py` - Change pricing logic
- `app/models.py` - Add fields

### **For Deployment:**
- `render.yaml` OR `docs/HEROKU_DEPLOYMENT.md`
- Follow one guide completely

### **Never Touch:**
- `parse_orange_json.py` (works as-is)
- `database_schema.sql` (stable)
- `app/database.py` (query layer is complete)

---

## 💡 Pro Tips

1. **Lost in the code?** Start with `app/main.py` endpoints
2. **Testing locally?** Use `docker-compose up -d`
3. **Need to understand pricing?** Read `app/calculator.py` with `tests/test_calculator.py` side-by-side
4. **Deploying?** Pick ONE guide (Render or Heroku) and follow it completely
5. **Updating data?** Only run `parse_orange_json.py` monthly

---

## 📞 Quick Reference Card

**Print this and keep nearby:**

```
┌────────────────────────────────────────────────────┐
│  ORANGE API - QUICK REFERENCE                      │
├────────────────────────────────────────────────────┤
│  Start API:    docker-compose up -d                │
│  View Docs:    http://localhost:8000/docs          │
│  Import Data:  python parse_orange_json.py ...     │
│  Run Tests:    pytest tests/                       │
│  Get Schema:   curl .../openapi.yaml               │
├────────────────────────────────────────────────────┤
│  Main Endpoint: POST /bundles/calculate            │
│  Cost: €14/mo (Render) or €34/mo (Heroku)         │
│  Token Savings: 96% (48K → 1.5K)                   │
└────────────────────────────────────────────────────┘
```

---

**You're now oriented! 🧭**

Which file would you like to explore first?
