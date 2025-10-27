"""
Database Operations for Orange Belgium API
=========================================
All database queries and operations
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor
import json

from app.models import (
    ProductDetail, OptionBase, GroupBase,
    PriceRuleBase, PromotionBase, Rule,
    CalculationMethod, PromoType, RuleType
)


class DatabaseConnection:
    """Database connection manager"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.conn = None
    
    def connect(self):
        """Establish database connection"""
        self.conn = psycopg2.connect(self.connection_string)
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def get_cursor(self):
        """Get cursor with RealDictCursor"""
        return self.conn.cursor(cursor_factory=RealDictCursor)
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class OrangeDatabase:
    """Main database operations class"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
    # ========================================================================
    # PRODUCT QUERIES
    # ========================================================================
    
    def get_products(
        self,
        group_id: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        keyword: Optional[str] = None,
        is_active: bool = True
    ) -> List[ProductDetail]:
        """
        Get products with optional filters.
        
        Args:
            group_id: Filter by group ID
            min_price: Minimum monthly price
            max_price: Maximum monthly price
            keyword: Search in product name
            is_active: Only active products
            
        Returns:
            List of ProductDetail objects
        """
        with DatabaseConnection(self.connection_string) as db:
            cursor = db.get_cursor()
            
            query = """
                SELECT 
                    p.id, p.internal_name, p.display_name, p.slug, p.epc_id,
                    p.group_id, p.monthly_price, p.activation_fee, p.device_fee,
                    p.installation_fee, p.specs, p.description,
                    p.card_title, p.card_subtitle,
                    g.name as group_name
                FROM products p
                LEFT JOIN groups g ON p.group_id = g.id
                WHERE p.is_active = %s
            """
            params = [is_active]
            
            if group_id:
                query += " AND p.group_id = %s"
                params.append(group_id)
            
            if min_price is not None:
                query += " AND p.monthly_price >= %s"
                params.append(min_price)
            
            if max_price is not None:
                query += " AND p.monthly_price <= %s"
                params.append(max_price)
            
            if keyword:
                query += " AND (p.display_name ILIKE %s OR p.description ILIKE %s)"
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            
            query += " ORDER BY p.group_id, p.weight, p.monthly_price"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [self._row_to_product(row) for row in rows]
    
    def get_product_by_id(self, product_id: str) -> Optional[ProductDetail]:
        """Get single product by ID"""
        products = self.get_products_by_ids([product_id])
        return products[0] if products else None
    
    def get_products_by_ids(self, product_ids: List[str]) -> List[ProductDetail]:
        """Get multiple products by IDs"""
        if not product_ids:
            return []
        
        with DatabaseConnection(self.connection_string) as db:
            cursor = db.get_cursor()
            
            query = """
                SELECT 
                    p.id, p.internal_name, p.display_name, p.slug, p.epc_id,
                    p.group_id, p.monthly_price, p.activation_fee, p.device_fee,
                    p.installation_fee, p.specs, p.description,
                    p.card_title, p.card_subtitle,
                    g.name as group_name
                FROM products p
                LEFT JOIN groups g ON p.group_id = g.id
                WHERE p.id = ANY(%s) AND p.is_active = TRUE
            """
            
            cursor.execute(query, (product_ids,))
            rows = cursor.fetchall()
            
            return [self._row_to_product(row) for row in rows]
    
    # ========================================================================
    # OPTION QUERIES
    # ========================================================================
    
    def get_options(self, is_active: bool = True) -> List[OptionBase]:
        """Get all options"""
        with DatabaseConnection(self.connection_string) as db:
            cursor = db.get_cursor()
            
            query = """
                SELECT id, name, monthly_price, option_type, description
                FROM options
                WHERE is_active = %s
                ORDER BY monthly_price
            """
            
            cursor.execute(query, (is_active,))
            rows = cursor.fetchall()
            
            return [self._row_to_option(row) for row in rows]
    
    def get_options_by_ids(self, option_ids: List[str]) -> List[OptionBase]:
        """Get multiple options by IDs"""
        if not option_ids:
            return []
        
        with DatabaseConnection(self.connection_string) as db:
            cursor = db.get_cursor()
            
            query = """
                SELECT id, name, monthly_price, option_type, description
                FROM options
                WHERE id = ANY(%s) AND is_active = TRUE
            """
            
            cursor.execute(query, (option_ids,))
            rows = cursor.fetchall()
            
            return [self._row_to_option(row) for row in rows]
    
    # ========================================================================
    # GROUP QUERIES
    # ========================================================================
    
    def get_groups(self) -> List[GroupBase]:
        """Get all product groups"""
        with DatabaseConnection(self.connection_string) as db:
            cursor = db.get_cursor()
            
            query = """
                SELECT id, name, slug
                FROM groups
                ORDER BY display_order
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            return [
                GroupBase(
                    id=row['id'],
                    name=row['name'],
                    slug=row['slug']
                )
                for row in rows
            ]
    
    # ========================================================================
    # BUNDLE VALIDATION
    # ========================================================================
    
    def can_bundle_products(self, product_ids: List[str]) -> tuple[bool, Optional[str]]:
        """
        Check if products can be bundled together.
        
        Returns:
            (is_valid, configurator_id)
        """
        if not product_ids:
            return False, None
        
        with DatabaseConnection(self.connection_string) as db:
            cursor = db.get_cursor()
            
            # Find configurators that contain ALL the given products
            query = """
                SELECT 
                    c.id,
                    c.name,
                    COUNT(DISTINCT cp.product_id) as matching_products
                FROM configurators c
                JOIN configurator_products cp ON c.configurator_id = cp.configurator_id
                WHERE cp.product_id = ANY(%s)
                GROUP BY c.id, c.name
                HAVING COUNT(DISTINCT cp.product_id) = %s
            """
            
            cursor.execute(query, (product_ids, len(product_ids)))
            row = cursor.fetchone()
            
            if row:
                return True, row['id']
            
            return False, None
    
    def get_compatible_options(self, product_ids: List[str]) -> List[OptionBase]:
        """Get options that are compatible with given products"""
        with DatabaseConnection(self.connection_string) as db:
            cursor = db.get_cursor()
            
            # Find configurators that contain these products
            query = """
                SELECT DISTINCT o.id, o.name, o.monthly_price, o.option_type, o.description
                FROM options o
                JOIN configurator_options co ON o.id = co.option_id
                JOIN configurator_products cp ON co.configurator_id = cp.configurator_id
                WHERE cp.product_id = ANY(%s)
                  AND o.is_active = TRUE
            """
            
            cursor.execute(query, (product_ids,))
            rows = cursor.fetchall()
            
            return [self._row_to_option(row) for row in rows]
    
    # ========================================================================
    # PRICE RULES
    # ========================================================================
    
    def get_price_rules(self, is_active: bool = True) -> List[PriceRuleBase]:
        """Get all price rules (permanent bundle discounts)"""
        with DatabaseConnection(self.connection_string) as db:
            cursor = db.get_cursor()
            
            query = """
                SELECT 
                    id, name, description, calculation_method, calculation_value,
                    rules, calculation_order, legal_summary, legal_info
                FROM price_rules
                WHERE is_active = %s
                ORDER BY calculation_order
            """
            
            cursor.execute(query, (is_active,))
            rows = cursor.fetchall()
            
            return [self._row_to_price_rule(row) for row in rows]
    
    def get_price_rules_for_products(self, product_ids: List[str]) -> List[PriceRuleBase]:
        """Get price rules that apply to specific products"""
        if not product_ids:
            return []
        
        with DatabaseConnection(self.connection_string) as db:
            cursor = db.get_cursor()
            
            query = """
                SELECT DISTINCT
                    pr.id, pr.name, pr.description, pr.calculation_method, 
                    pr.calculation_value, pr.rules, pr.calculation_order,
                    pr.legal_summary, pr.legal_info
                FROM price_rules pr
                JOIN price_rule_products prp ON pr.id = prp.price_rule_id
                WHERE prp.product_id = ANY(%s)
                  AND pr.is_active = TRUE
                ORDER BY pr.calculation_order
            """
            
            cursor.execute(query, (product_ids,))
            rows = cursor.fetchall()
            
            return [self._row_to_price_rule(row) for row in rows]
    
    # ========================================================================
    # PROMOTIONS
    # ========================================================================
    
    def get_active_promotions(
        self,
        as_of_date: Optional[datetime] = None
    ) -> List[PromotionBase]:
        """
        Get promotions active on a specific date.
        
        Args:
            as_of_date: Date to check (default: now)
            
        Returns:
            List of active promotions
        """
        if as_of_date is None:
            as_of_date = datetime.now()
        
        with DatabaseConnection(self.connection_string) as db:
            cursor = db.get_cursor()
            
            query = """
                SELECT 
                    id, name, promo_type, calculation_method, calculation_value,
                    duration_months, start_date, end_date, rules, calculation_order,
                    excluded_promos, legal_summary, legal_info
                FROM promotions
                WHERE is_active = TRUE
                  AND start_date <= %s
                  AND end_date >= %s
                ORDER BY calculation_order
            """
            
            cursor.execute(query, (as_of_date, as_of_date))
            rows = cursor.fetchall()
            
            return [self._row_to_promotion(row) for row in rows]
    
    def get_promotions_for_products(
        self,
        product_ids: List[str],
        as_of_date: Optional[datetime] = None
    ) -> List[PromotionBase]:
        """Get active promotions that apply to specific products"""
        if not product_ids:
            return []
        
        if as_of_date is None:
            as_of_date = datetime.now()
        
        with DatabaseConnection(self.connection_string) as db:
            cursor = db.get_cursor()
            
            query = """
                SELECT DISTINCT
                    p.id, p.name, p.promo_type, p.calculation_method, 
                    p.calculation_value, p.duration_months, p.start_date, p.end_date,
                    p.rules, p.calculation_order, p.excluded_promos,
                    p.legal_summary, p.legal_info
                FROM promotions p
                LEFT JOIN promotion_products pp ON p.id = pp.promotion_id
                WHERE p.is_active = TRUE
                  AND p.start_date <= %s
                  AND p.end_date >= %s
                  AND (pp.product_id = ANY(%s) OR pp.product_id IS NULL)
                ORDER BY p.calculation_order
            """
            
            cursor.execute(query, (as_of_date, as_of_date, product_ids))
            rows = cursor.fetchall()
            
            return [self._row_to_promotion(row) for row in rows]
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _row_to_product(self, row: Dict) -> ProductDetail:
        """Convert database row to ProductDetail"""
        return ProductDetail(
            id=row['id'],
            internal_name=row.get('internal_name'),
            display_name=row['display_name'],
            slug=row['slug'],
            epc_id=row.get('epc_id'),
            group_id=row['group_id'],
            monthly_price=Decimal(str(row['monthly_price'])),
            activation_fee=Decimal(str(row.get('activation_fee', 0))),
            device_fee=Decimal(str(row.get('device_fee', 0))),
            installation_fee=Decimal(str(row.get('installation_fee', 0))),
            specs=row.get('specs', {}),
            description=row.get('description'),
            card_title=row.get('card_title'),
            card_subtitle=row.get('card_subtitle'),
            group_name=row.get('group_name')
        )
    
    def _row_to_option(self, row: Dict) -> OptionBase:
        """Convert database row to OptionBase"""
        return OptionBase(
            id=row['id'],
            name=row['name'],
            monthly_price=Decimal(str(row['monthly_price'])),
            option_type=row.get('option_type'),
            description=row.get('description')
        )
    
    def _row_to_price_rule(self, row: Dict) -> PriceRuleBase:
        """Convert database row to PriceRuleBase"""
        rules_json = row.get('rules', [])
        if isinstance(rules_json, str):
            rules_json = json.loads(rules_json)
        
        return PriceRuleBase(
            id=row['id'],
            name=row['name'],
            calculation_method=CalculationMethod(row['calculation_method']),
            calculation_value=Decimal(str(row['calculation_value'])),
            rules=[Rule(**r) for r in rules_json]
        )
    
    def _row_to_promotion(self, row: Dict) -> PromotionBase:
        """Convert database row to PromotionBase"""
        rules_json = row.get('rules', [])
        if isinstance(rules_json, str):
            rules_json = json.loads(rules_json)
        
        excluded_json = row.get('excluded_promos', [])
        if isinstance(excluded_json, str):
            excluded_json = json.loads(excluded_json)
        
        return PromotionBase(
            id=row['id'],
            name=row['name'],
            promo_type=PromoType(row['promo_type']),
            calculation_method=CalculationMethod(row['calculation_method']),
            calculation_value=Decimal(str(row['calculation_value'])),
            duration_months=row['duration_months'],
            start_date=row['start_date'],
            end_date=row['end_date'],
            rules=[Rule(**r) for r in rules_json],
            excluded_promos=excluded_json,
            legal_summary=row.get('legal_summary')
        )
