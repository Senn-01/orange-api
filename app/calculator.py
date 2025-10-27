"""
Orange Belgium Pricing Calculator
=================================
Core engine for calculating bundle prices with promotions and discounts.

This module handles:
1. Rule evaluation (checking if promotions/discounts apply)
2. Discount stacking (applying multiple promotions correctly)
3. Timeline generation (month-by-month breakdown)
"""

from typing import List, Dict, Tuple, Optional
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass

from app.models import (
    ProductDetail, OptionBase, PriceRuleBase, PromotionBase,
    AppliedDiscount, MonthlyBreakdown, PricingSummary,
    BundleCalculation, BundleContext, Rule, RuleType,
    CalculationMethod
)


# ============================================================================
# RULE EVALUATION ENGINE
# ============================================================================

class RuleEvaluator:
    """Evaluates eligibility rules for price rules and promotions"""
    
    @staticmethod
    def evaluate_rule(rule: Rule, context: BundleContext) -> bool:
        """
        Evaluate a single rule against the bundle context.
        
        Args:
            rule: The rule to evaluate
            context: Current bundle context (products, options, groups)
            
        Returns:
            True if rule passes, False otherwise
        """
        rule_type = rule.type
        params = rule.parameters
        
        if rule_type == RuleType.HAS_PRODUCT:
            # Must have at least one of the specified products
            return any(pid in context.product_ids for pid in params)
        
        elif rule_type == RuleType.HAS_PRODUCT_IN_GROUP:
            # Must have at least one product from specified group
            group_id = params[0] if params else None
            if not group_id:
                return False
            
            # Check if any product in bundle is from this group
            return any(
                p.group_id == group_id 
                for p in context.products
            )
        
        elif rule_type == RuleType.HAS_ONLY_PRODUCT_IN_GROUP:
            # ONLY products from this group (no products from other groups)
            group_id = params[0] if params else None
            if not group_id:
                return False
            
            # All products must be from this group
            return all(
                p.group_id == group_id 
                for p in context.products
            )
        
        elif rule_type == RuleType.HAS_OPTION:
            # Must have at least one of the specified options
            return any(oid in context.option_ids for oid in params)
        
        elif rule_type == RuleType.ITEM_NUMBER:
            # Check cart item count (rarely used)
            required_count = int(params[0]) if params else 0
            return len(context.product_ids) == required_count
        
        elif rule_type == RuleType.ITEM_MIN:
            # Minimum number of items from a list
            if len(params) < 2:
                return False
            
            min_count = int(params[0])
            item_list = params[1] if isinstance(params[1], list) else params[1:]
            
            matching_count = sum(
                1 for pid in context.product_ids 
                if pid in item_list
            )
            
            return matching_count >= min_count
        
        else:
            # Unknown rule type - fail safe
            return False
    
    @staticmethod
    def evaluate_rules(rules: List[Rule], context: BundleContext) -> bool:
        """
        Evaluate ALL rules (they must ALL pass - AND logic).
        
        Args:
            rules: List of rules to evaluate
            context: Bundle context
            
        Returns:
            True if ALL rules pass, False if any fail
        """
        if not rules:
            return True  # No rules = always eligible
        
        return all(
            RuleEvaluator.evaluate_rule(rule, context)
            for rule in rules
        )


# ============================================================================
# DISCOUNT CALCULATOR
# ============================================================================

class DiscountCalculator:
    """Calculate discount amounts based on method and value"""
    
    @staticmethod
    def calculate_discount(
        base_price: Decimal,
        method: CalculationMethod,
        value: Decimal
    ) -> Decimal:
        """
        Calculate the discount amount.
        
        Args:
            base_price: Original price
            method: How to calculate (amount, percentage, free)
            value: Discount value (euro amount or percentage)
            
        Returns:
            Discount amount (always positive)
        """
        if method == CalculationMethod.AMOUNT:
            # Fixed euro amount
            return min(value, base_price)  # Don't exceed base price
        
        elif method == CalculationMethod.PERCENTAGE:
            # Percentage of base price
            return base_price * (value / Decimal('100'))
        
        elif method == CalculationMethod.FREE:
            # Completely free
            return base_price
        
        else:
            return Decimal('0')


# ============================================================================
# PRICING CALCULATOR ENGINE
# ============================================================================

@dataclass
class DiscountApplication:
    """Internal representation of a discount to apply"""
    id: str
    name: str
    discount_type: str  # 'price_rule' or 'promotion'
    amount: Decimal
    duration_months: Optional[int]  # None = permanent
    calculation_order: int
    applies_to_product_id: Optional[str] = None


class PricingCalculator:
    """Main pricing calculation engine"""
    
    def __init__(
        self,
        context: BundleContext,
        price_rules: List[PriceRuleBase],
        promotions: List[PromotionBase]
    ):
        self.context = context
        self.price_rules = price_rules
        self.promotions = promotions
        self.evaluator = RuleEvaluator()
    
    def calculate(self) -> BundleCalculation:
        """
        Calculate complete bundle pricing.
        
        Returns:
            BundleCalculation with timeline and summary
        """
        # 1. Calculate base prices
        base_total = self._calculate_base_price()
        
        # 2. Find eligible permanent discounts (price rules)
        eligible_price_rules = self._find_eligible_price_rules()
        
        # 3. Find eligible promotions (time-limited)
        eligible_promotions = self._find_eligible_promotions()
        
        # 4. Calculate discount applications
        price_rule_discounts = self._apply_price_rules(eligible_price_rules)
        promotion_discounts = self._apply_promotions(eligible_promotions)
        
        # 5. Calculate totals
        permanent_discount_total = sum(d.amount for d in price_rule_discounts)
        promotion_discount_total = sum(d.amount for d in promotion_discounts)
        
        # 6. Build month-by-month timeline
        monthly_breakdown = self._build_timeline(
            base_total,
            price_rule_discounts,
            promotion_discounts
        )
        
        # 7. Build summary
        summary = self._build_summary(monthly_breakdown)
        
        # 8. Convert to response models
        applied_price_rules = [
            AppliedDiscount(
                id=d.id,
                name=d.name,
                type='price_rule',
                discount_amount=d.amount,
                duration_months=None,  # Permanent
                applies_to_product=d.applies_to_product_id
            )
            for d in price_rule_discounts
        ]
        
        applied_promotions = [
            AppliedDiscount(
                id=d.id,
                name=d.name,
                type='promotion',
                discount_amount=d.amount,
                duration_months=d.duration_months,
                applies_to_product=d.applies_to_product_id
            )
            for d in promotion_discounts
        ]
        
        return BundleCalculation(
            products=self.context.products,
            options=self.context.options,
            base_monthly_total=base_total,
            permanent_discount_total=permanent_discount_total,
            promotion_discount_total=promotion_discount_total,
            applied_price_rules=applied_price_rules,
            applied_promotions=applied_promotions,
            monthly_breakdown=monthly_breakdown,
            summary=summary,
            is_valid_bundle=True
        )
    
    def _calculate_base_price(self) -> Decimal:
        """Calculate base monthly price (sum of all products + options)"""
        product_total = sum(p.monthly_price for p in self.context.products)
        option_total = sum(o.monthly_price for o in self.context.options)
        return product_total + option_total
    
    def _find_eligible_price_rules(self) -> List[PriceRuleBase]:
        """Find price rules that apply to this bundle"""
        eligible = []
        
        for rule in self.price_rules:
            # Check if bundle meets rule criteria
            if self.evaluator.evaluate_rules(rule.rules, self.context):
                eligible.append(rule)
        
        return eligible
    
    def _find_eligible_promotions(self) -> List[PromotionBase]:
        """Find promotions that apply to this bundle"""
        eligible = []
        current_date = self.context.calculation_date
        
        for promo in self.promotions:
            # Check date validity
            if not (promo.start_date <= current_date <= promo.end_date):
                continue
            
            # Check if bundle meets promo criteria
            if not self.evaluator.evaluate_rules(promo.rules, self.context):
                continue
            
            # Check if promo applies to any product in bundle
            # (promo must target at least one product we have)
            # Note: This is inferred from JSON - promotions have productIDs
            # For now, we assume the promo is eligible if rules pass
            # In production, you'd also check promotion_products table
            
            eligible.append(promo)
        
        # Handle exclusions
        eligible = self._resolve_exclusions(eligible)
        
        return eligible
    
    def _resolve_exclusions(self, promotions: List[PromotionBase]) -> List[PromotionBase]:
        """
        Handle promotion exclusions (excludedPromos).
        
        If two promotions conflict, keep the one with better calculationOrder
        (lower = higher priority).
        """
        if not promotions:
            return promotions
        
        # Build exclusion map
        excluded_ids = set()
        for promo in promotions:
            if promo.excluded_promos:
                excluded_ids.update(promo.excluded_promos)
        
        # Filter out excluded promotions
        # Keep the one with better (lower) calculationOrder
        promo_by_id = {p.id: p for p in promotions}
        
        # Remove directly excluded promos
        result = []
        for promo in promotions:
            if promo.id in excluded_ids:
                # Check if there's a conflicting promo with better order
                conflicting = [
                    p for p in promotions
                    if promo.id in p.excluded_promos
                ]
                
                if conflicting:
                    best_conflicting = min(conflicting, key=lambda p: p.calculation_order)
                    if best_conflicting.calculation_order < promo.calculation_order:
                        # Skip this promo, keep the better one
                        continue
            
            result.append(promo)
        
        return result
    
    def _apply_price_rules(self, rules: List[PriceRuleBase]) -> List[DiscountApplication]:
        """
        Apply price rules and calculate discount amounts.
        
        For now, we apply all eligible rules (they stack).
        """
        discounts = []
        
        for rule in rules:
            # Calculate discount
            # Note: In production, you'd need to determine which product
            # the discount applies to from price_rule_products table
            # For simplicity, we apply to the base total
            
            amount = DiscountCalculator.calculate_discount(
                base_price=self._calculate_base_price(),
                method=rule.calculation_method,
                value=rule.calculation_value
            )
            
            discounts.append(DiscountApplication(
                id=rule.id,
                name=rule.name,
                discount_type='price_rule',
                amount=amount,
                duration_months=None,  # Permanent
                calculation_order=rule.calculation_order
            ))
        
        # Sort by calculation order
        discounts.sort(key=lambda d: d.calculation_order)
        
        return discounts
    
    def _apply_promotions(self, promotions: List[PromotionBase]) -> List[DiscountApplication]:
        """
        Apply promotions and calculate discount amounts.
        
        Promotions stack unless explicitly excluded.
        """
        discounts = []
        
        for promo in promotions:
            amount = DiscountCalculator.calculate_discount(
                base_price=self._calculate_base_price(),
                method=promo.calculation_method,
                value=promo.calculation_value
            )
            
            discounts.append(DiscountApplication(
                id=promo.id,
                name=promo.name,
                discount_type='promotion',
                amount=amount,
                duration_months=promo.duration_months,
                calculation_order=promo.calculation_order
            ))
        
        # Sort by calculation order
        discounts.sort(key=lambda d: d.calculation_order)
        
        return discounts
    
    def _build_timeline(
        self,
        base_price: Decimal,
        price_rule_discounts: List[DiscountApplication],
        promotion_discounts: List[DiscountApplication]
    ) -> List[MonthlyBreakdown]:
        """
        Build month-by-month cost breakdown.
        
        Logic:
        - Month 1: Base + all discounts + one-time fees
        - Months 2-X: Base + all discounts (until shortest promo expires)
        - Months X+1-Y: Base + remaining discounts
        - Months Y+: Base + permanent discounts only
        """
        timeline = []
        
        # Calculate one-time fees (activation, installation)
        one_time_fees = sum(
            p.activation_fee + p.installation_fee 
            for p in self.context.products
        )
        
        # Determine promotion end months
        promo_durations = [
            d.duration_months for d in promotion_discounts 
            if d.duration_months
        ]
        
        if not promo_durations:
            # No time-limited promotions
            shortest_promo = 0
        else:
            shortest_promo = min(promo_durations)
        
        # Build timeline for requested duration
        for month in range(1, self.context.duration_months + 1):
            # Permanent discounts apply always
            permanent_discount = sum(d.amount for d in price_rule_discounts)
            
            # Temporary discounts apply until duration expires
            temporary_discount = sum(
                d.amount for d in promotion_discounts
                if d.duration_months is None or month <= d.duration_months
            )
            
            monthly_cost = base_price - permanent_discount - temporary_discount
            
            # One-time fees only in month 1
            fees = one_time_fees if month == 1 else Decimal('0')
            
            timeline.append(MonthlyBreakdown(
                month=month,
                base_price=base_price,
                permanent_discounts=permanent_discount,
                temporary_discounts=temporary_discount,
                total_monthly=monthly_cost,
                one_time_fees=fees,
                total_due=monthly_cost + fees
            ))
        
        return timeline
    
    def _build_summary(self, timeline: List[MonthlyBreakdown]) -> PricingSummary:
        """Build cost summary from timeline"""
        
        if not timeline:
            return PricingSummary(
                first_month_total=Decimal('0'),
                promotional_period_monthly=Decimal('0'),
                promotional_period_months=0,
                permanent_monthly=Decimal('0'),
                first_year_total=Decimal('0'),
                second_year_total=Decimal('0')
            )
        
        # Find when promotions end (when temporary_discounts becomes 0)
        promo_end_month = 0
        for breakdown in timeline:
            if breakdown.temporary_discounts > 0:
                promo_end_month = breakdown.month
        
        # Calculate totals
        first_month = timeline[0]
        promo_period_months = promo_end_month if promo_end_month > 0 else 0
        
        # Promotional period monthly (average if varied, or just month 2)
        if promo_end_month > 1:
            promo_monthly = timeline[1].total_monthly  # Month 2 (no one-time fees)
        else:
            promo_monthly = first_month.total_monthly
        
        # Permanent monthly (after promos end)
        permanent_monthly = timeline[-1].total_monthly
        
        # Year totals
        first_year = sum(
            breakdown.total_due 
            for breakdown in timeline[:min(12, len(timeline))]
        )
        
        second_year = sum(
            breakdown.total_due 
            for breakdown in timeline[12:min(24, len(timeline))]
        ) if len(timeline) > 12 else Decimal('0')
        
        return PricingSummary(
            first_month_total=first_month.total_due,
            promotional_period_monthly=promo_monthly,
            promotional_period_months=promo_period_months,
            permanent_monthly=permanent_monthly,
            first_year_total=first_year,
            second_year_total=second_year
        )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def calculate_bundle_pricing(
    context: BundleContext,
    price_rules: List[PriceRuleBase],
    promotions: List[PromotionBase]
) -> BundleCalculation:
    """
    Convenience function to calculate bundle pricing.
    
    Args:
        context: Bundle context
        price_rules: All available price rules
        promotions: All available promotions
        
    Returns:
        Complete bundle calculation
    """
    calculator = PricingCalculator(context, price_rules, promotions)
    return calculator.calculate()
