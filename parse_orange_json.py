"""
Orange Belgium JSON Parser
==========================
Parses the Orange API JSON and populates PostgreSQL database.
Run this monthly or when Orange updates their product catalog.

Usage:
    python parse_orange_json.py --json orange_full.json --db-url postgresql://user:pass@localhost/orange
"""

import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2.extras import execute_batch
import argparse


class OrangeJSONParser:
    """Parse Orange Belgium JSON and insert into database"""
    
    def __init__(self, db_connection_string: str):
        self.conn = psycopg2.connect(db_connection_string)
        self.cursor = self.conn.cursor()
        self.stats = {
            'groups': 0,
            'products': 0,
            'options': 0,
            'configurators': 0,
            'price_rules': 0,
            'promotions': 0,
            'errors': []
        }
    
    def parse_and_import(self, json_file_path: str) -> Dict[str, int]:
        """Main entry point - parse JSON and import all entities"""
        print(f"📂 Loading JSON from: {json_file_path}")
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("🗑️  Clearing existing data...")
        self._clear_database()
        
        print("📊 Importing groups...")
        self._import_groups(data.get('groups', []))
        
        print("📦 Importing products...")
        self._import_products(data.get('products', []))
        
        print("🔌 Importing options...")
        self._import_options(data.get('options', []))
        
        print("🔗 Importing configurators...")
        self._import_configurators(data.get('products', []))
        
        print("💰 Importing price rules...")
        self._import_price_rules(data.get('priceRules', []))
        
        print("🎁 Importing promotions...")
        self._import_promotions(data.get('promotions', []))
        
        print("✅ Committing transaction...")
        self.conn.commit()
        
        print("📝 Logging sync...")
        self._log_sync(json_file_path, 'success')
        
        return self.stats
    
    def _clear_database(self):
        """Clear all data (cascade deletes will handle junctions)"""
        tables = [
            'promo_codes',
            'promotion_options',
            'promotion_products',
            'promotions',
            'price_rule_products',
            'price_rules',
            'configurator_options',
            'configurator_products',
            'configurators',
            'options',
            'products',
            'groups'
        ]
        
        for table in tables:
            self.cursor.execute(f"DELETE FROM {table}")
    
    def _import_groups(self, groups: List[Dict]) -> None:
        """Import product groups (Internet, Mobile, TV, Extra)"""
        
        if not groups:
            print("⚠️  No groups found in JSON")
            return
        
        query = """
            INSERT INTO groups (id, name, slug, display_order)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                slug = EXCLUDED.slug,
                display_order = EXCLUDED.display_order
        """
        
        data = [
            (
                group['_id'],
                group['name'],
                group.get('slug', group['name'].lower()),
                i  # Use array position as display order
            )
            for i, group in enumerate(groups)
        ]
        
        execute_batch(self.cursor, query, data)
        self.stats['groups'] = len(data)
        print(f"   ✓ Imported {len(data)} groups")
    
    def _import_products(self, products: List[Dict]) -> None:
        """Import main products (Internet, Mobile, TV)"""
        
        # Filter out configurators (they're not real products)
        real_products = [
            p for p in products 
            if 'Configurateur' not in p.get('name', '')
        ]
        
        if not real_products:
            print("⚠️  No products found in JSON")
            return
        
        query = """
            INSERT INTO products (
                id, internal_name, display_name, slug, epc_id, group_id,
                monthly_price, device_fee, activation_fee, installation_fee,
                specs, description, card_title, card_subtitle, summary_title, modal_content,
                weight, labels, rules, footprints, is_active
            )
            VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
            ON CONFLICT (id) DO UPDATE SET
                display_name = EXCLUDED.display_name,
                monthly_price = EXCLUDED.monthly_price,
                activation_fee = EXCLUDED.activation_fee
        """
        
        data = []
        for product in real_products:
            specs_obj = product.get('specs', {})
            price = product.get('price', {})
            
            data.append((
                product['_id'],
                product.get('_name'),
                product['name'],
                product.get('slug', ''),
                product.get('epcID'),
                product.get('groupID'),
                price.get('monthlyPrice', 0),
                price.get('deviceFee', 0),
                price.get('activationFee', 0),
                price.get('installationFee', 0),
                json.dumps(specs_obj) if specs_obj else '{}',
                specs_obj.get('description', ''),
                specs_obj.get('cardtitle', ''),
                specs_obj.get('cardsubtitle', ''),
                specs_obj.get('summarytitle', ''),
                specs_obj.get('modal', ''),
                product.get('_weight', 0),
                json.dumps(product.get('label', [])),
                json.dumps(product.get('rules', [])),
                json.dumps(product.get('_footprints', [])),
                True
            ))
        
        execute_batch(self.cursor, query, data)
        self.stats['products'] = len(data)
        print(f"   ✓ Imported {len(data)} products")
    
    def _import_options(self, options: List[Dict]) -> None:
        """Import add-on options (Netflix, WiFi Comfort, etc.)"""
        
        if not options:
            print("⚠️  No options found in JSON")
            return
        
        query = """
            INSERT INTO options (
                id, name, slug, description, monthly_price, device_fee, activation_fee,
                option_type, specs, is_active
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                monthly_price = EXCLUDED.monthly_price
        """
        
        data = []
        for option in options:
            price = option.get('price', {})
            
            data.append((
                option['_id'],
                option['name'],
                option.get('slug', ''),
                option.get('description', ''),
                price.get('monthlyPrice', 0),
                price.get('deviceFee', 0),
                price.get('activationFee', 0),
                option.get('type', 'addon'),
                json.dumps(option.get('specs', {})),
                True
            ))
        
        execute_batch(self.cursor, query, data)
        self.stats['options'] = len(data)
        print(f"   ✓ Imported {len(data)} options")
    
    def _import_configurators(self, products: List[Dict]) -> None:
        """Import configurators and their product/option relationships"""
        
        # Find configurator products
        configurators = [
            p for p in products 
            if 'Configurateur' in p.get('name', '')
        ]
        
        if not configurators:
            print("⚠️  No configurators found in JSON")
            return
        
        # Insert configurators
        query_conf = """
            INSERT INTO configurators (id, name, slug, weight, is_active)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
        """
        
        conf_data = [
            (
                conf['_id'],
                conf['name'],
                conf.get('slug', ''),
                conf.get('_weight', 0),
                True
            )
            for conf in configurators
        ]
        
        execute_batch(self.cursor, query_conf, conf_data)
        
        # Insert configurator-product relationships
        query_prod = """
            INSERT INTO configurator_products (configurator_id, product_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """
        
        prod_data = []
        for conf in configurators:
            for product_id in conf.get('productIDs', []):
                prod_data.append((conf['_id'], product_id))
        
        if prod_data:
            execute_batch(self.cursor, query_prod, prod_data)
        
        # Insert configurator-option relationships
        query_opt = """
            INSERT INTO configurator_options (configurator_id, option_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """
        
        opt_data = []
        for conf in configurators:
            for option_id in conf.get('optionIDs', []):
                opt_data.append((conf['_id'], option_id))
        
        if opt_data:
            execute_batch(self.cursor, query_opt, opt_data)
        
        self.stats['configurators'] = len(configurators)
        print(f"   ✓ Imported {len(configurators)} configurators")
        print(f"   ✓ Linked {len(prod_data)} products, {len(opt_data)} options")
    
    def _import_price_rules(self, price_rules: List[Dict]) -> None:
        """Import permanent bundle discounts (Avantage multi-produits)"""
        
        if not price_rules:
            print("⚠️  No price rules found in JSON")
            return
        
        # Insert price rules
        query_rule = """
            INSERT INTO price_rules (
                id, name, description, calculation_method, calculation_value,
                rules, calculation_order, legal_summary, legal_info, is_active
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                calculation_value = EXCLUDED.calculation_value,
                rules = EXCLUDED.rules
        """
        
        rule_data = []
        for i, rule in enumerate(price_rules):
            calc = rule.get('calculation', {})
            
            # Generate ID if not present
            rule_id = rule.get('_id', f'PR{i:04d}')
            
            rule_data.append((
                rule_id,
                rule.get('name', f'Price Rule {i+1}'),
                rule.get('description', ''),
                calc.get('method', 'amount'),
                calc.get('value', 0),
                json.dumps(rule.get('rules', [])),
                rule.get('calculationOrder', 50),
                rule.get('legalSummary', ''),
                rule.get('legalInfo', ''),
                True
            ))
        
        execute_batch(self.cursor, query_rule, rule_data)
        
        # Insert price rule - product relationships
        query_prod = """
            INSERT INTO price_rule_products (price_rule_id, product_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """
        
        prod_data = []
        for i, rule in enumerate(price_rules):
            rule_id = rule.get('_id', f'PR{i:04d}')
            for product_id in rule.get('productIDs', []):
                prod_data.append((rule_id, product_id))
        
        if prod_data:
            execute_batch(self.cursor, query_prod, prod_data)
        
        self.stats['price_rules'] = len(rule_data)
        print(f"   ✓ Imported {len(rule_data)} price rules")
        print(f"   ✓ Linked to {len(prod_data)} products")
    
    def _import_promotions(self, promotions: List[Dict]) -> None:
        """Import time-limited promotional offers"""
        
        if not promotions:
            print("⚠️  No promotions found in JSON")
            return
        
        # Insert promotions
        query_promo = """
            INSERT INTO promotions (
                id, name, promo_type, calculation_method, calculation_value, duration_months,
                start_date, end_date, rules, calculation_order, excluded_promos,
                labels, specs, legal_summary, legal_info, is_choice, is_active
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
                calculation_value = EXCLUDED.calculation_value
        """
        
        promo_data = []
        for promo in promotions:
            calc = promo.get('calculation', {})
            
            try:
                start_date = datetime.fromisoformat(promo['startDate'].replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(promo['endDate'].replace('Z', '+00:00'))
            except Exception as e:
                print(f"   ⚠️  Invalid dates for promo {promo['_id']}: {e}")
                continue
            
            promo_data.append((
                promo['_id'],
                promo.get('name', 'Unnamed Promotion'),
                promo.get('type', 'discount'),
                calc.get('method', 'amount'),
                calc.get('value', 0),
                calc.get('duration', 0),
                start_date,
                end_date,
                json.dumps(promo.get('rules', [])),
                promo.get('calculationOrder', 50),
                json.dumps(promo.get('excludedPromos', [])),
                json.dumps(promo.get('label', [])),
                json.dumps(promo.get('specs', {})),
                promo.get('legalSummary', ''),
                promo.get('legalInfo', ''),
                promo.get('isChoice', False),
                True
            ))
        
        execute_batch(self.cursor, query_promo, promo_data)
        
        # Insert promotion - product relationships
        query_prod = """
            INSERT INTO promotion_products (promotion_id, product_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """
        
        prod_data = []
        for promo in promotions:
            for product_id in promo.get('productIDs', []):
                prod_data.append((promo['_id'], product_id))
        
        if prod_data:
            execute_batch(self.cursor, query_prod, prod_data)
        
        # Insert promotion - option relationships
        query_opt = """
            INSERT INTO promotion_options (promotion_id, option_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """
        
        opt_data = []
        for promo in promotions:
            for option_id in promo.get('optionIDs', []):
                opt_data.append((promo['_id'], option_id))
        
        if opt_data:
            execute_batch(self.cursor, query_opt, opt_data)
        
        self.stats['promotions'] = len(promo_data)
        print(f"   ✓ Imported {len(promo_data)} promotions")
        print(f"   ✓ Linked to {len(prod_data)} products, {len(opt_data)} options")
    
    def _log_sync(self, source_file: str, status: str) -> None:
        """Log the data sync operation"""
        query = """
            INSERT INTO data_sync_log (
                source_url, records_imported, sync_status, metadata
            )
            VALUES (%s, %s, %s, %s)
        """
        
        self.cursor.execute(query, (
            source_file,
            sum(self.stats.values()),
            status,
            json.dumps(self.stats)
        ))
        self.conn.commit()
    
    def close(self):
        """Close database connection"""
        self.cursor.close()
        self.conn.close()
    
    def print_summary(self):
        """Print import summary"""
        print("\n" + "="*60)
        print("📊 IMPORT SUMMARY")
        print("="*60)
        for key, value in self.stats.items():
            if key != 'errors':
                print(f"   {key:.<20} {value:>5}")
        
        if self.stats['errors']:
            print(f"\n⚠️  {len(self.stats['errors'])} errors occurred:")
            for error in self.stats['errors']:
                print(f"   - {error}")
        
        print("="*60)


def main():
    parser = argparse.ArgumentParser(description='Parse Orange Belgium JSON and populate database')
    parser.add_argument('--json', required=True, help='Path to orange_full.json')
    parser.add_argument('--db-url', required=True, help='PostgreSQL connection string')
    parser.add_argument('--dry-run', action='store_true', help='Parse but don\'t commit')
    
    args = parser.parse_args()
    
    try:
        print("🚀 Starting Orange JSON import...")
        print(f"   JSON: {args.json}")
        print(f"   Database: {args.db_url}")
        print()
        
        parser_obj = OrangeJSONParser(args.db_url)
        stats = parser_obj.parse_and_import(args.json)
        
        if args.dry_run:
            print("\n🔄 DRY RUN - Rolling back changes...")
            parser_obj.conn.rollback()
        
        parser_obj.print_summary()
        parser_obj.close()
        
        print("\n✅ Import completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during import: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
