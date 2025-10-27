#!/usr/bin/env python3
"""
Orange Belgium Data Refresh Script
===================================
Fetches latest Orange data and updates database.

Runs monthly via GitHub Actions or manually:
    python refresh_orange_data.py
"""

import os
import sys
import json
import tempfile
import requests
from datetime import datetime
from typing import Dict, Optional
import subprocess

# Import our parser
from parse_orange_json import OrangeJSONParser


# ============================================================================
# CONFIGURATION
# ============================================================================

ORANGE_API_URL = "https://www.orange.be/fr/api/obe-dps/v1"
DATABASE_URL = os.getenv("DATABASE_URL")
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")  # Optional

# Validation thresholds
MIN_PRODUCTS = 10  # Expect at least 10 products
MIN_PROMOTIONS = 5  # Expect at least 5 promotions


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def log(message: str) -> None:
    """Print with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def send_alert(message: str, error: bool = False) -> None:
    """Send alert to Slack (if configured)"""
    if not SLACK_WEBHOOK:
        return
    
    try:
        emoji = "🚨" if error else "✅"
        requests.post(
            SLACK_WEBHOOK,
            json={"text": f"{emoji} {message}"},
            timeout=5
        )
    except Exception as e:
        log(f"Failed to send Slack alert: {e}")


def fetch_orange_data() -> Dict:
    """Fetch latest JSON from Orange API"""
    log("📡 Fetching data from Orange API...")
    
    try:
        response = requests.get(ORANGE_API_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        log(f"✅ Fetched {len(response.content)} bytes")
        return data
    
    except requests.RequestException as e:
        log(f"❌ Failed to fetch Orange data: {e}")
        raise


def validate_json_structure(data: Dict) -> bool:
    """Basic validation: check required sections and minimum counts"""
    log("🔍 Validating JSON structure...")
    
    # Check required top-level keys
    required_keys = ['products', 'promotions', 'groups', 'options']
    missing_keys = [key for key in required_keys if key not in data]
    
    if missing_keys:
        log(f"❌ Missing required keys: {missing_keys}")
        return False
    
    # Check product count
    product_count = len(data.get('products', []))
    if product_count < MIN_PRODUCTS:
        log(f"❌ Only {product_count} products (expected >={MIN_PRODUCTS})")
        return False
    
    # Check promotion count
    promo_count = len(data.get('promotions', []))
    if promo_count < MIN_PROMOTIONS:
        log(f"⚠️  Only {promo_count} promotions (expected >={MIN_PROMOTIONS})")
        # Don't fail - promotions might legitimately be low
    
    # Check first product has required fields
    if data['products']:
        product = data['products'][0]
        required_fields = ['_id', 'name', 'price', 'groupID']
        missing = [f for f in required_fields if f not in product]
        
        if missing:
            log(f"❌ Product missing fields: {missing}")
            return False
    
    log(f"✅ Validation passed: {product_count} products, {promo_count} promotions")
    return True


def backup_database() -> Optional[str]:
    """Create database backup (PostgreSQL only)"""
    log("💾 Creating database backup...")
    
    try:
        # Generate backup filename
        backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        backup_path = os.path.join(tempfile.gettempdir(), backup_file)
        
        # Use pg_dump to backup
        # Note: DATABASE_URL format: postgresql://user:pass@host:port/dbname
        subprocess.run(
            ["pg_dump", DATABASE_URL, "-f", backup_path],
            check=True,
            capture_output=True
        )
        
        # Check backup size
        backup_size = os.path.getsize(backup_path)
        if backup_size < 1024:  # Less than 1KB is suspicious
            log(f"⚠️  Backup seems too small: {backup_size} bytes")
            return None
        
        log(f"✅ Backup created: {backup_path} ({backup_size} bytes)")
        return backup_path
    
    except subprocess.CalledProcessError as e:
        log(f"⚠️  Backup failed: {e}")
        log("Continuing without backup (risky!)")
        return None
    except Exception as e:
        log(f"⚠️  Backup error: {e}")
        return None


def import_data(json_file: str) -> Dict[str, int]:
    """Import Orange data into database"""
    log("📥 Importing data to database...")
    
    parser = OrangeJSONParser(DATABASE_URL)
    stats = parser.parse_and_import(json_file)
    parser.close()
    
    return stats


def run_smoke_tests() -> bool:
    """Run basic tests to verify data is working"""
    log("🧪 Running smoke tests...")
    
    try:
        from app.database import OrangeDatabase
        
        db = OrangeDatabase(DATABASE_URL)
        
        # Test 1: Can get products
        products = db.get_products()
        if len(products) < MIN_PRODUCTS:
            log(f"❌ Smoke test failed: only {len(products)} products")
            return False
        
        # Test 2: Can get promotions
        promotions = db.get_active_promotions()
        log(f"ℹ️  Found {len(promotions)} active promotions")
        
        # Test 3: Can validate bundle
        if len(products) >= 2:
            is_valid, _ = db.can_bundle_products([products[0].id, products[1].id])
            log(f"ℹ️  Bundle validation test: {is_valid}")
        
        log("✅ Smoke tests passed")
        return True
    
    except Exception as e:
        log(f"❌ Smoke test failed: {e}")
        return False


def restore_backup(backup_file: str) -> bool:
    """Restore database from backup"""
    log(f"🔄 Restoring backup from {backup_file}...")
    
    try:
        subprocess.run(
            ["psql", DATABASE_URL, "-f", backup_file],
            check=True,
            capture_output=True
        )
        log("✅ Backup restored")
        return True
    except subprocess.CalledProcessError as e:
        log(f"❌ Restore failed: {e}")
        return False


# ============================================================================
# MAIN REFRESH PIPELINE
# ============================================================================

def refresh_pipeline() -> bool:
    """Main refresh pipeline"""
    
    log("="*60)
    log("🚀 Starting Orange data refresh pipeline")
    log("="*60)
    
    backup_file = None
    temp_json = None
    
    try:
        # Step 1: Fetch new data
        data = fetch_orange_data()
        
        # Step 2: Validate structure
        if not validate_json_structure(data):
            send_alert("Validation failed - JSON structure changed", error=True)
            log("❌ Aborting: Validation failed")
            return False
        
        # Step 3: Save to temporary file
        temp_json = os.path.join(tempfile.gettempdir(), "orange_new.json")
        with open(temp_json, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        log(f"📝 Saved to: {temp_json}")
        
        # Step 4: Backup current database
        backup_file = backup_database()
        if not backup_file:
            log("⚠️  No backup created - proceeding anyway")
        
        # Step 5: Import new data
        stats = import_data(temp_json)
        
        log("="*60)
        log("📊 Import Statistics:")
        for key, value in stats.items():
            if key != 'errors':
                log(f"   {key}: {value}")
        log("="*60)
        
        # Step 6: Run smoke tests
        if not run_smoke_tests():
            log("❌ Smoke tests failed!")
            
            if backup_file:
                log("Attempting to restore backup...")
                if restore_backup(backup_file):
                    send_alert("Import failed, backup restored", error=True)
                else:
                    send_alert("CRITICAL: Import failed AND restore failed!", error=True)
            else:
                send_alert("Import failed, no backup available!", error=True)
            
            return False
        
        # Success!
        log("="*60)
        log("✅ Refresh completed successfully!")
        log("="*60)
        
        send_alert(
            f"Orange data refresh successful: "
            f"{stats.get('products', 0)} products, "
            f"{stats.get('promotions', 0)} promotions"
        )
        
        return True
    
    except Exception as e:
        log(f"❌ Pipeline failed: {e}")
        
        # Attempt restore if we have a backup
        if backup_file:
            log("Attempting to restore backup...")
            restore_backup(backup_file)
        
        send_alert(f"Refresh pipeline failed: {str(e)}", error=True)
        return False
    
    finally:
        # Cleanup temp files
        if temp_json and os.path.exists(temp_json):
            try:
                os.remove(temp_json)
                log(f"🗑️  Cleaned up: {temp_json}")
            except:
                pass


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Entry point"""
    
    # Check database URL is configured
    if not DATABASE_URL:
        log("❌ DATABASE_URL not set!")
        log("Set environment variable: export DATABASE_URL=postgresql://...")
        sys.exit(1)
    
    # Run refresh
    success = refresh_pipeline()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
