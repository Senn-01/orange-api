# Resilience Strategy - Orange JSON Changes

**How the system handles Orange Belgium API changes**

---

## 🎯 Design Philosophy

**Pragmatic, not paranoid:**
- ✅ Protect against common failures
- ✅ Fail gracefully with rollback
- ⚠️ Alert on anomalies
- 🚫 Don't over-engineer for unlikely scenarios

---

## 📊 Risk Assessment

### What Could Orange Change?

| Change Type | Probability | Impact | Our Protection |
|-------------|-------------|--------|----------------|
| **New products added** | 🟢 High (monthly) | Low | ✅ Automatic |
| **New promotions** | 🟢 High (monthly) | Low | ✅ Automatic |
| **Price changes** | 🟢 High (monthly) | Low | ✅ Automatic |
| **New optional fields** | 🟡 Medium (quarterly) | Low | ✅ Ignored safely |
| **Required field removed** | 🟡 Medium (yearly?) | High | ✅ Validation catches |
| **Structure reorganized** | 🔴 Low (rare) | High | ✅ Validation + Manual |
| **New discount types** | 🔴 Low (rare) | Medium | ⚠️ Manual update needed |
| **New rule types** | 🔴 Low (rare) | Medium | ⚠️ Fails safe (excluded) |

---

## 🛡️ Protection Layers

### Layer 1: Validation ✅

**Before importing any data:**

```python
def validate_json_structure(data):
    # Check 1: Required sections exist
    if 'products' not in data:
        ❌ ABORT - Missing products section
    
    # Check 2: Reasonable counts
    if len(data['products']) < 10:
        ❌ ABORT - Too few products (was: 15)
    
    # Check 3: Required fields present
    product = data['products'][0]
    if '_id' not in product or 'price' not in product:
        ❌ ABORT - Product structure changed
    
    ✅ SAFE TO IMPORT
```

**Catches:**
- Missing sections
- Corrupted data
- Major structure changes

**Doesn't catch:**
- New optional fields (safe - ignored)
- Field type changes (caught later)

---

### Layer 2: Backup + Rollback ✅

**Before importing:**

```
Current DB State
    ↓
💾 pg_dump → backup.sql
    ↓
Import new data
    ↓
🧪 Smoke tests
    ↓
✅ Success?
    ├─ YES → ✅ Done, delete backup
    └─ NO  → 🔄 psql < backup.sql (restore)
```

**Protects against:**
- Bad imports
- Data corruption
- Calculation errors discovered later

**Limitations:**
- Backup is temporary (deleted after success)
- No long-term history (add S3 upload if needed)

---

### Layer 3: Smoke Tests ✅

**After import, verify:**

```python
def run_smoke_tests():
    # Can query products?
    products = db.get_products()
    if len(products) < 10:
        ❌ FAIL - Import didn't work
    
    # Can query promotions?
    promotions = db.get_active_promotions()
    # (just check it doesn't crash)
    
    # Can validate bundles?
    is_valid = db.can_bundle_products(['54801', '54831'])
    # (just check it doesn't crash)
    
    ✅ PASS - Basic functionality works
```

**Catches:**
- Database constraint violations
- Type mismatches
- Import partially failed

**Optional enhancement:**
```python
# Add known-good test
calculation = calculate_bundle(['54801', '54831'])
if calculation.base_monthly_total != Decimal('81.00'):
    ⚠️ WARNING - Known bundle price changed
```

---

### Layer 4: Alerting 🔔

**You get notified when:**

```
✅ Success
"Orange data refresh successful: 15 products, 34 promotions"

❌ Validation Failed
"🚨 Validation failed - JSON structure changed"
→ Manual review needed

❌ Import Failed
"🚨 Import failed, backup restored"
→ API still working with old data

🚨 CRITICAL: Restore Failed
"🚨 Import failed AND restore failed!"
→ Urgent manual intervention
```

**Delivery:**
- Slack (if configured)
- GitHub Actions log
- Email (GitHub notifications)

---

## 🔄 Failure Scenarios

### Scenario 1: Orange API Down

```
📡 Fetching data from Orange API...
❌ Failed to fetch Orange data: Connection timeout

Result:
- Import aborted
- Database unchanged
- API continues with old data
- Alert sent
- Auto-retry next month
```

**Impact:** Low (API works, just with last month's data)

---

### Scenario 2: Orange Changed Field Name

```
📡 Fetching data...
✅ Fetched 142567 bytes
🔍 Validating JSON structure...
❌ Product missing fields: ['price']

Result:
- Import aborted (validation failed)
- Database unchanged
- API continues with old data
- Alert sent: "Validation failed - JSON structure changed"
- Manual review needed
```

**Impact:** Medium (need to update parser)

**Fix:**
```python
# Update parse_orange_json.py
# Old: product.get('price', {})
# New: product.get('pricing', {})  # Orange renamed field
```

---

### Scenario 3: Orange Added New Discount Type

```
📡 Fetching data...
✅ Validation passed
💾 Backup created
📥 Importing...
✅ Imported successfully
🧪 Smoke tests...
✅ Passed

But... API returns incorrect prices!

Result:
- Import succeeded
- Smoke tests passed
- But calculations wrong
- Discover when testing API
```

**Impact:** Medium (prices incorrect until fix)

**Fix:**
```python
# Update app/calculator.py
# Add new calculation method
if method == CalculationMethod.NEW_TYPE:
    return calculate_new_type(base_price, value)
```

**Prevention:** Add price validation to smoke tests

---

### Scenario 4: Database Restore Fails

```
📥 Importing...
❌ Constraint violation
🔄 Restoring backup...
❌ Restore failed: File not found

Result:
- Database partially imported
- Backup restore failed
- API may return errors
- 🚨 CRITICAL ALERT sent
```

**Impact:** High (manual intervention needed)

**Recovery:**
```bash
# 1. Check database state
psql $DATABASE_URL -c "SELECT COUNT(*) FROM products"

# 2. If empty/broken, re-import from last known good
python parse_orange_json.py --json orange_backup.json

# 3. Verify API
curl https://api/health
```

**Prevention:** Test pg_dump/restore in CI pipeline

---

## 📈 Change History Tracking

**Recommended: Store historical JSONs**

```python
# In refresh_orange_data.py
def save_historical_json(data):
    """Save JSON to archive"""
    filename = f"orange_{datetime.now().strftime('%Y%m%d')}.json"
    
    # Option 1: S3
    s3.upload_json(data, f'archive/{filename}')
    
    # Option 2: Git repo
    with open(f'data/archive/{filename}', 'w') as f:
        json.dump(data, f)
    
    # Useful for:
    # - Debugging issues
    # - Comparing changes over time
    # - Rolling back to specific date
```

**Benefit:** Can diff any two months to see what changed

---

## 🔍 Diff Detection (Optional Enhancement)

```python
def compare_with_last_month(new_data, old_data):
    """Generate change report"""
    
    # Products changed?
    old_ids = {p['_id'] for p in old_data['products']}
    new_ids = {p['_id'] for p in new_data['products']}
    
    report = {
        'products_added': new_ids - old_ids,
        'products_removed': old_ids - new_ids,
        'promotions_added': len(new_data['promotions']) - len(old_data['promotions']),
        'field_changes': detect_field_changes(old_data, new_data)
    }
    
    # Send summary
    if report['products_removed']:
        send_alert(f"⚠️ Products removed: {report['products_removed']}")
    
    return report
```

**Use case:** Know exactly what changed month-over-month

---

## 🧪 Testing Strategy

### Manual Testing (Before Each Release)

```bash
# 1. Fetch current Orange JSON
curl https://www.orange.be/fr/api/obe-dps/v1 > test.json

# 2. Run parser locally
python parse_orange_json.py --json test.json --db-url localhost

# 3. Verify API works
curl http://localhost:8000/bundles/calculate -X POST ...

# 4. Check known prices
# Internet 500 + Mobile Medium should be €81 base
```

### Automated Testing (CI Pipeline)

```yaml
# .github/workflows/test.yml
- name: Test with current Orange data
  run: |
    curl https://www.orange.be/fr/api/obe-dps/v1 > test.json
    python parse_orange_json.py --json test.json --db-url test_db
    pytest tests/ -v
```

**Catches breaking changes before deployment**

---

## 📋 Monitoring Checklist

**Monthly Review (after refresh runs):**

- [ ] Refresh succeeded
- [ ] Product count stable (~15)
- [ ] Promotion count reasonable (5-40)
- [ ] No validation errors
- [ ] Smoke tests passed
- [ ] API response time normal
- [ ] Known bundle still calculates correctly

**Quarterly Review:**

- [ ] Check Orange documentation for API changes
- [ ] Review historical JSON for trends
- [ ] Update validation thresholds if needed
- [ ] Test with sample queries

**Yearly Review:**

- [ ] Audit all rule types still supported
- [ ] Check for new Orange features
- [ ] Review backup/restore procedures
- [ ] Load test with current data volume

---

## 🎓 Lessons Learned (Add Yours Here)

**Document Orange-specific quirks:**

- [ ] _Did Orange ever change JSON without notice?_
- [ ] _What was the impact?_
- [ ] _How did we fix it?_
- [ ] _How can we prevent it next time?_

**Template:**
```
Date: YYYY-MM-DD
Change: Orange added new field "newField"
Impact: None (parser ignored it)
Action: No action needed
Learning: Extra fields are safe to ignore
```

---

## 🏁 Summary

**Our resilience strategy:**

```
┌─────────────────────────────────────────┐
│ 1. Validation (catches structure changes) │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ 2. Backup (enables rollback)            │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ 3. Import (with error handling)         │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ 4. Smoke Tests (verifies functionality) │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ 5. Alerting (notifies on issues)        │
└─────────────────────────────────────────┘
```

**Result:**
- ✅ Handles routine changes automatically
- ✅ Catches breaking changes before damage
- ✅ Can rollback on failure
- ✅ Alerts humans when needed
- ✅ Keeps API running even if refresh fails

**Philosophy:** 
Automate the 95% of cases that are routine. Alert humans for the 5% that need judgment.

---

**This is pragmatic resilience: simple, safe, and maintainable.** ✅
