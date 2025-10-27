# Orange Belgium API - Complete JSON Analysis

**Date:** October 27, 2025  
**Purpose:** Build API to help Nexus Agent guide customers and calculate precise subscription costs

---

## 1. Entity Relationship Diagram

```
┌─────────────┐
│   CONTEXT   │
│             │
│ - language  │
│ - footprint │ (region: Wallonie)
└─────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                          GROUPS (4 total)                             │
├──────────────────────────────────────────────────────────────────────┤
│  54776: Internet    │  54781: Mobile    │  54786: TV    │  54791: Extra │
└──────────────────────────────────────────────────────────────────────┘
         │                     │                   │              │
         ↓                     ↓                   ↓              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       PRODUCTS (15 total)                            │
├─────────────────────────────────────────────────────────────────────┤
│  INTERNET (6):                                                       │
│    54796: 200 Mbps        €51/mo                                    │
│    54801: 500 Mbps        €59/mo                                    │
│    54806: 1000 Mbps       €69/mo                                    │
│    55406: 200 + Netflix   €65.99/mo                                 │
│    54816: 500 + Netflix   €73.99/mo                                 │
│    54811: 1000 + Netflix  €83.99/mo                                 │
│                                                                      │
│  MOBILE (4):                                                         │
│    54821: Child           €5/mo                                      │
│    54826: Small           €15/mo                                     │
│    54831: Medium          €22/mo                                     │
│    54836: Large           €39/mo                                     │
│                                                                      │
│  TV (3):                                                             │
│    54841: TV Lite         €10/mo                                     │
│    54846: TV              €20/mo                                     │
│    55436: TV Plus         €30/mo                                     │
│                                                                      │
│  CONFIGURATORS (2):                                                  │
│    54896: Configurateur   (links 10 products + 10 options)          │
│    54901: Config Netflix  (links 9 products + 9 options)            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ can add
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         OPTIONS (9 total)                            │
├─────────────────────────────────────────────────────────────────────┤
│  54891: Netflix              €14.99/mo                               │
│  54856: My Comfort Service   €10/mo                                  │
│  54851: WiFi Comfort         €3/mo                                   │
│  54866: Be tv                €15/mo                                  │
│  55441: Orange TV Family     €15/mo                                  │
│  54871: Orange Sport         €15/mo                                  │
│  54876: Fixed Phone          €12/mo                                  │
│  54881: Google Chromecast    €0/mo                                   │
│  54886: Extra décodeur       €9/mo                                   │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                    PRICE RULES (14 total)                             │
├──────────────────────────────────────────────────────────────────────┤
│  Bundle discounts when combining products from different groups       │
│  Examples:                                                            │
│    - €4 off when Internet + Mobile                                    │
│    - €5.99 off on Internet 1 Gbps + Netflix option                   │
│    - €5 off when Internet 1000 Mbps + specific products              │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                     PROMOTIONS (34 total)                             │
├──────────────────────────────────────────────────────────────────────┤
│  Time-limited discounts on specific products/bundles                  │
│  Types: discount (31), activationFee (2), data (1)                   │
│  Methods: amount (30), percentage (1), free (3)                      │
│  Duration: typically 6 or 12 months                                  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Product Types & Key Fields

### **2.1 Core Product Structure**

Every product has:

```json
{
  "_id": "54801",                    // Unique identifier
  "_name": "Zen Fiber",              // Internal name
  "name": "Internet illimité 500 Mbps", // Display name
  "slug": "net-m",                   // URL-friendly identifier
  "epcID": "AO005017",               // External Product Code (for billing)
  "groupID": "54776",                // Group: Internet/Mobile/TV/Extra
  
  "price": {
    "monthlyPrice": 59,              // Base monthly cost
    "deviceFee": 0,                  // Device/equipment cost
    "activationFee": 39,             // One-time activation
    "installationFee": 0             // One-time installation
  },
  
  "productIDs": [],                  // Compatible/included product IDs
  "optionIDs": [],                   // Compatible option IDs
  
  "specs": {
    "description": "...",            // HTML description
    "cardtitle": "500 Mbps",        // Short display title
    "modal": "...",                  // Full modal content
    "cardsubtitle": "Zen Fiber *",  // Subtitle
    "summarytitle": "500 Mbps"      // Summary display
  },
  
  "rules": [],                       // Product-specific rules
  "label": [],                       // Display labels (badges)
  "_footprints": []                  // Regional availability
}
```

### **2.2 Product Categories**

| Group ID | Category | Products | Price Range | Activation Fee |
|----------|----------|----------|-------------|----------------|
| **54776** | Internet | 6 | €51 - €83.99/mo | €39 |
| **54781** | Mobile | 4 | €5 - €39/mo | €0 |
| **54786** | TV | 3 | €10 - €30/mo | €0 |
| **54791** | Extra | 2 configurators | €0 | €0 |

### **2.3 Options (Add-ons)**

Options can be added to main products:

| ID | Name | Monthly Cost | Purpose |
|----|------|--------------|---------|
| 54891 | Netflix | €14.99 | Streaming |
| 54856 | My Comfort Service | €10 | Support |
| 54851 | WiFi Comfort | €3 | WiFi optimization |
| 54866 | Be tv | €15 | TV channels |
| 55441 | Orange TV Family | €15 | Family TV package |
| 54871 | Orange Sport | €15 | Sports channels |
| 54876 | Fixed Phone | €12 | Landline |
| 54881 | Google Chromecast | €0 | Streaming device |
| 54886 | Extra décodeur | €9 | Additional decoder |

---

## 3. How Products Reference Each Other

### **3.1 Configurators (Bundle Templates)**

Configurators define valid product combinations:

```json
{
  "_id": "54896",
  "name": "Configurateur",
  "productIDs": [
    "54796", "54801", "54806",  // Internet options
    "54821", "54826", "54831", "54836",  // Mobile options
    "54846", "54841", "55436"   // TV options
  ],
  "optionIDs": [
    "54856", "54851", "54861",  // Service options
    "54871", "54866", "54876",  // Add-on options
    "54881", "54886", "54891", "55441"
  ]
}
```

**Meaning:** These products can be combined together. Agent can pick 1 from each group.

### **3.2 Reference Patterns**

**Pattern 1: Bundle Validation**
```
User selects: Internet 500 + Mobile Medium
API checks: Are both IDs in same configurator's productIDs?
Result: YES → Valid bundle
```

**Pattern 2: Option Compatibility**
```
User adds: Netflix option (54891) to Internet 500
API checks: Is 54891 in configurator's optionIDs?
Result: YES → Compatible
```

**Pattern 3: Cross-Group Bundles**
```
"Love" bundle = Internet (54776) + Mobile (54781) ± TV (54786)
Triggers: Special price rules and promotions
```

---

## 4. Promotion Structure

### **4.1 Promotion Types**

| Type | Count | Purpose | Example |
|------|-------|---------|---------|
| **discount** | 31 | Price reduction | -€15/mo for 6 months |
| **activationFee** | 2 | Waive activation | Free activation |
| **data** | 1 | Extra mobile data | Bonus GB |

### **4.2 Calculation Methods**

```json
{
  "calculation": {
    "method": "amount",      // "amount", "percentage", or "free"
    "value": 15,            // €15 or 50%
    "duration": 6           // Months (6 or 12 typically)
  }
}
```

**Method Types:**
- **amount**: Fixed euro discount (e.g., -€15)
- **percentage**: Percentage discount (e.g., -50%)
- **free**: Completely free for duration

### **4.3 Promotion Rules**

Promotions apply based on rules:

```json
{
  "rules": [
    {
      "type": "hasProductInGroup",
      "parameters": ["54781"]  // Must have a Mobile product
    },
    {
      "type": "hasProduct",
      "parameters": ["54831", "54836"]  // Must have Medium or Large
    }
  ]
}
```

**Rule Types:**
1. **hasProductInGroup**: Must have ANY product from group (e.g., any Mobile)
2. **hasProduct**: Must have SPECIFIC product(s)
3. **hasOnlyProductInGroup**: Must have ONLY products from this group
4. **hasOption**: Must have specific option
5. **itemNumber**: Relates to cart item position
6. **itemMin**: Minimum number of items from list

### **4.4 Promotion Eligibility Logic**

**Example 1: "Love Bundle" Promotion**
```json
{
  "_id": "55441",
  "name": "Promo : -15€ pendant 12 mois",
  "calculation": {"method": "amount", "value": 15, "duration": 12},
  "productIDs": ["54801"],  // Applies to Internet 500
  "rules": [
    {"type": "hasProductInGroup", "parameters": ["54781"]}  // Need Mobile
  ]
}
```

**Interpretation:**
- IF customer has Internet 500 (54801)
- AND has any Mobile product (group 54781)
- THEN get €15 off Internet 500 for 12 months

**Example 2: Time-Limited Web Promo**
```json
{
  "_id": "55371",
  "name": "Web promo : -20€ pendant 12 mois",
  "calculation": {"method": "amount", "value": 20, "duration": 12},
  "startDate": "2025-02-18T07:00:00",
  "endDate": "2025-03-05T06:59:59",
  "productIDs": ["54801", "54816"],
  "rules": [
    {"type": "hasProduct", "parameters": ["54831", "54836", "54826"]}
  ],
  "excludedPromos": ["55396"]  // Cannot combine with promo 55396
}
```

**Interpretation:**
- Valid: Feb 18 - Mar 5, 2025
- IF customer has Internet 500 OR 500+Netflix
- AND has Mobile Small/Medium/Large
- AND NOT using promo 55396
- THEN get €20 off for 12 months

### **4.5 Promotion Stacking**

Some promotions can stack, others exclude each other:

```json
{
  "calculationOrder": 33,        // Lower = applied first
  "excludedPromos": ["55396"]    // Cannot combine with these
}
```

**Stacking Rules:**
1. Promotions apply in `calculationOrder` sequence
2. Check `excludedPromos` array for conflicts
3. Most promotions can stack unless explicitly excluded

---

## 5. Pricing Calculation Logic

### **5.1 Price Components**

```
TOTAL COST = Base Monthly + Options - Price Rules - Promotions + Fees
```

**Base Monthly:**
```
Product base price (e.g., Internet 500 = €59)
```

**Options:**
```
+ Netflix (€14.99)
+ WiFi Comfort (€3)
= +€17.99
```

**Price Rules (Bundle Discounts):**
```
Example: Internet + Mobile = -€4/mo (permanent)
```

**Promotions (Time-Limited):**
```
Example: -€15/mo for first 6 months
```

**One-Time Fees:**
```
+ Activation fee (€39, one-time)
```

### **5.2 Complete Calculation Example**

**Scenario:** Customer wants Internet 500 + Mobile Medium + Netflix

**Step 1: Base Prices**
```
Internet 500 (54801):     €59.00/mo
Mobile Medium (54831):    €22.00/mo
Netflix option (54891):   €14.99/mo
─────────────────────────────────
Subtotal:                 €95.99/mo
```

**Step 2: Apply Price Rules**
```
Rule: "Avantage multi-produits" (-€4 when Internet + Mobile)
New subtotal:             €91.99/mo
```

**Step 3: Apply Promotions** (assuming eligible)
```
Promo 1: Internet 500 -€15 for 12 months
Promo 2: Internet+Netflix -€5.99 for 6 months
```

**Monthly Breakdown:**
```
Months 1-6:   €91.99 - €15 - €5.99 = €71.00/mo
Months 7-12:  €91.99 - €15         = €76.99/mo
Months 13+:   €91.99/mo (permanent price)
```

**Step 4: One-Time Fees**
```
Activation (Internet):    €39 (month 1 only)
```

**Final Cost Simulation:**
```
Month 1:      €71.00 + €39 = €110.00
Months 2-6:   €71.00/mo
Months 7-12:  €76.99/mo
Months 13+:   €91.99/mo
───────────────────────────────────
Year 1 Total: €71 + (5×€71) + (6×€76.99) + €39 = €916.94
Year 2 Total: 12×€91.99 = €1,103.88
```

### **5.3 Price Rules Structure**

```json
{
  "name": "Avantage multi-produits",
  "calculation": {
    "method": "amount",
    "value": 4
  },
  "productIDs": ["54796", "54801", "54806"],  // Applies to these
  "rules": [
    {"type": "hasProductInGroup", "parameters": ["54776"]},  // Has Internet
    {"type": "hasProductInGroup", "parameters": ["54781"]}   // Has Mobile
  ]
}
```

**Interpretation:** 
- IF customer has ANY Internet product (from group 54776)
- AND has ANY Mobile product (from group 54781)
- THEN apply €4 discount to the Internet products listed

---

## 6. API Design Requirements

### **6.1 Critical Data for Agent**

To answer: *"What's my cost for Internet 500 + Mobile Medium over 12 months?"*

Agent needs:
1. ✅ **Base prices** (monthly + fees)
2. ✅ **Valid combinations** (can these products bundle?)
3. ✅ **Bundle discounts** (price rules)
4. ✅ **Active promotions** (time-limited offers)
5. ✅ **Month-by-month breakdown** (promotional periods)

### **6.2 Recommended API Endpoints**

**GET /products**
```
Query: ?groupID=54776&maxPrice=60
Returns: Filtered products (500-800 tokens)
```

**GET /bundles/validate**
```
Body: {"productIDs": ["54801", "54831"]}
Returns: {valid: true, discounts: [...], totalPrice: 77.99}
```

**GET /promotions/active**
```
Query: ?productIDs=54801,54831&date=2025-10-27
Returns: Applicable promotions with rules (400-600 tokens)
```

**GET /pricing/calculate** ⭐ **MOST CRITICAL**
```
Body: {
  "productIDs": ["54801", "54831"],
  "optionIDs": ["54891"],
  "duration": 12
}
Returns: {
  "monthly": [
    {"month": 1, "base": 95.99, "discounts": -20.99, "total": 114.00, "fees": 39},
    {"month": 2, "base": 95.99, "discounts": -20.99, "total": 75.00},
    ...
  ],
  "summary": {
    "year1Total": 916.94,
    "year2Total": 1103.88,
    "permanentMonthly": 91.99
  }
}
```

**GET /options**
```
Query: ?productID=54801
Returns: Compatible options for this product
```

### **6.3 Database Schema (Suggested)**

**products**
- id, name, slug, epc_id, group_id
- monthly_price, activation_fee, device_fee, installation_fee
- specs (JSON), metadata (JSON)

**options**
- id, name, monthly_price, type

**product_compatibility**
- product_id, compatible_product_id (for bundles)
- product_id, option_id (for options)

**price_rules**
- id, name, method, value, calculation_order
- applies_to_products (array), rules (JSON)

**promotions**
- id, name, type, method, value, duration
- start_date, end_date, calculation_order
- applies_to_products (array), rules (JSON)
- excluded_promos (array)

**groups**
- id, name, slug, description

---

## 7. Key Insights for Implementation

### **7.1 Complexity Drivers**

1. **Time-based promotions** expire and change frequently
2. **Rule evaluation** requires checking multiple conditions
3. **Stacking logic** needs careful ordering (calculationOrder)
4. **Regional availability** (footprints) may filter products

### **7.2 Token Optimization**

**Without API:** 48,000 tokens per query (entire JSON)  
**With API:** 1,500-3,000 tokens per query (calculated results)  
**Savings:** 94-96% token reduction

### **7.3 Calculation Responsibility**

❌ **DON'T:** Let agent calculate prices from raw data  
✅ **DO:** API calculates exact prices, agent explains to customer

**Why?**
- Deterministic (testable)
- Reliable (no LLM math errors)
- Maintainable (update rules in one place)
- Fast (pre-computed results)

### **7.4 Agent's Role**

1. Understand customer needs (budget, services)
2. Query API with relevant filters
3. Present options clearly
4. Explain cost breakdown from API response
5. Guide customer to best choice

### **7.5 Edge Cases to Handle**

- **Expired promotions:** Filter by current date
- **Excluded promotions:** Check exclusion rules
- **Regional restrictions:** Filter by footprint
- **Invalid combinations:** Validate before calculating
- **Option dependencies:** Some options require specific products

---

## Summary Statistics

| Entity | Count | Purpose |
|--------|-------|---------|
| **Products** | 15 | Main subscriptions (Internet, Mobile, TV) |
| **Groups** | 4 | Product categories |
| **Options** | 9 | Add-ons (Netflix, services) |
| **Price Rules** | 14 | Bundle discounts (permanent) |
| **Promotions** | 34 | Time-limited offers (6-12 months) |

**Total JSON Size:** 48K tokens  
**Target API Response:** 1.5-3K tokens per query  
**Reduction:** 94-96% ✅

---

*Ready for Phase 1: Database design & parsing implementation*
