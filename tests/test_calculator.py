"""
Tests for Orange Belgium API
============================
Test pricing calculations, rule evaluation, and API endpoints
"""

import pytest
from datetime import datetime
from decimal import Decimal

from app.models import (
    ProductDetail, OptionBase, PriceRuleBase, PromotionBase,
    Rule, RuleType, CalculationMethod, PromoType,
    BundleContext
)
from app.calculator import (
    RuleEvaluator, DiscountCalculator, PricingCalculator,
    calculate_bundle_pricing
)


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def sample_products():
    """Sample products for testing"""
    return [
        ProductDetail(
            id="54801",
            display_name="Internet 500 Mbps",
            slug="net-m",
            group_id="54776",
            monthly_price=Decimal("59.00"),
            activation_fee=Decimal("39.00"),
            specs={"speed": 500}
        ),
        ProductDetail(
            id="54831",
            display_name="Mobile Medium",
            slug="mob-m",
            group_id="54781",
            monthly_price=Decimal("22.00"),
            activation_fee=Decimal("0"),
            specs={"data": 15}
        )
    ]


@pytest.fixture
def sample_options():
    """Sample options for testing"""
    return [
        OptionBase(
            id="54891",
            name="Netflix",
            monthly_price=Decimal("14.99"),
            option_type="streaming"
        )
    ]


@pytest.fixture
def sample_price_rules():
    """Sample price rules (permanent discounts)"""
    return [
        PriceRuleBase(
            id="PR001",
            name="Avantage multi-produits Internet",
            calculation_method=CalculationMethod.AMOUNT,
            calculation_value=Decimal("4.00"),
            rules=[
                Rule(type=RuleType.HAS_PRODUCT_IN_GROUP, parameters=["54776"]),
                Rule(type=RuleType.HAS_PRODUCT_IN_GROUP, parameters=["54781"])
            ]
        ),
        PriceRuleBase(
            id="PR002",
            name="Avantage multi-produits Mobile",
            calculation_method=CalculationMethod.AMOUNT,
            calculation_value=Decimal("5.00"),
            rules=[
                Rule(type=RuleType.HAS_PRODUCT_IN_GROUP, parameters=["54776"]),
                Rule(type=RuleType.HAS_PRODUCT_IN_GROUP, parameters=["54781"])
            ]
        )
    ]


@pytest.fixture
def sample_promotions():
    """Sample promotions (time-limited)"""
    return [
        PromotionBase(
            id="PROMO001",
            name="Promo: -15€ pendant 6 mois",
            promo_type=PromoType.DISCOUNT,
            calculation_method=CalculationMethod.AMOUNT,
            calculation_value=Decimal("15.00"),
            duration_months=6,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 12, 31),
            rules=[
                Rule(type=RuleType.HAS_PRODUCT_IN_GROUP, parameters=["54781"])
            ],
            excluded_promos=[]
        )
    ]


@pytest.fixture
def bundle_context(sample_products, sample_options):
    """Sample bundle context"""
    return BundleContext(
        products=sample_products,
        options=[],
        product_ids=["54801", "54831"],
        option_ids=[],
        group_ids=["54776", "54781"],
        calculation_date=datetime(2025, 10, 27),
        duration_months=12
    )


# ============================================================================
# RULE EVALUATION TESTS
# ============================================================================

def test_rule_has_product(bundle_context):
    """Test HAS_PRODUCT rule evaluation"""
    evaluator = RuleEvaluator()
    
    # Should pass - has product 54801
    rule = Rule(type=RuleType.HAS_PRODUCT, parameters=["54801"])
    assert evaluator.evaluate_rule(rule, bundle_context) is True
    
    # Should pass - has at least one of the products
    rule = Rule(type=RuleType.HAS_PRODUCT, parameters=["54801", "99999"])
    assert evaluator.evaluate_rule(rule, bundle_context) is True
    
    # Should fail - doesn't have this product
    rule = Rule(type=RuleType.HAS_PRODUCT, parameters=["99999"])
    assert evaluator.evaluate_rule(rule, bundle_context) is False


def test_rule_has_product_in_group(bundle_context):
    """Test HAS_PRODUCT_IN_GROUP rule evaluation"""
    evaluator = RuleEvaluator()
    
    # Should pass - has product from Internet group
    rule = Rule(type=RuleType.HAS_PRODUCT_IN_GROUP, parameters=["54776"])
    assert evaluator.evaluate_rule(rule, bundle_context) is True
    
    # Should pass - has product from Mobile group
    rule = Rule(type=RuleType.HAS_PRODUCT_IN_GROUP, parameters=["54781"])
    assert evaluator.evaluate_rule(rule, bundle_context) is True
    
    # Should fail - no product from TV group
    rule = Rule(type=RuleType.HAS_PRODUCT_IN_GROUP, parameters=["54786"])
    assert evaluator.evaluate_rule(rule, bundle_context) is False


def test_rule_multiple_conditions(bundle_context):
    """Test evaluating multiple rules (AND logic)"""
    evaluator = RuleEvaluator()
    
    # Both conditions pass
    rules = [
        Rule(type=RuleType.HAS_PRODUCT_IN_GROUP, parameters=["54776"]),
        Rule(type=RuleType.HAS_PRODUCT_IN_GROUP, parameters=["54781"])
    ]
    assert evaluator.evaluate_rules(rules, bundle_context) is True
    
    # One condition fails
    rules = [
        Rule(type=RuleType.HAS_PRODUCT_IN_GROUP, parameters=["54776"]),
        Rule(type=RuleType.HAS_PRODUCT_IN_GROUP, parameters=["54786"])  # TV group
    ]
    assert evaluator.evaluate_rules(rules, bundle_context) is False


# ============================================================================
# DISCOUNT CALCULATION TESTS
# ============================================================================

def test_discount_amount():
    """Test fixed amount discount calculation"""
    calculator = DiscountCalculator()
    
    # Normal discount
    result = calculator.calculate_discount(
        base_price=Decimal("100"),
        method=CalculationMethod.AMOUNT,
        value=Decimal("15")
    )
    assert result == Decimal("15")
    
    # Discount larger than price (should cap at base price)
    result = calculator.calculate_discount(
        base_price=Decimal("10"),
        method=CalculationMethod.AMOUNT,
        value=Decimal("20")
    )
    assert result == Decimal("10")


def test_discount_percentage():
    """Test percentage discount calculation"""
    calculator = DiscountCalculator()
    
    result = calculator.calculate_discount(
        base_price=Decimal("100"),
        method=CalculationMethod.PERCENTAGE,
        value=Decimal("50")
    )
    assert result == Decimal("50")


def test_discount_free():
    """Test free discount (100% off)"""
    calculator = DiscountCalculator()
    
    result = calculator.calculate_discount(
        base_price=Decimal("100"),
        method=CalculationMethod.FREE,
        value=Decimal("0")
    )
    assert result == Decimal("100")


# ============================================================================
# PRICING CALCULATION TESTS
# ============================================================================

def test_base_price_calculation(bundle_context, sample_price_rules, sample_promotions):
    """Test base price calculation (sum of products)"""
    calculator = PricingCalculator(bundle_context, sample_price_rules, sample_promotions)
    
    base = calculator._calculate_base_price()
    # 59 + 22 = 81
    assert base == Decimal("81.00")


def test_price_rule_eligibility(bundle_context, sample_price_rules):
    """Test finding eligible price rules"""
    calculator = PricingCalculator(bundle_context, sample_price_rules, [])
    
    eligible = calculator._find_eligible_price_rules()
    
    # Both rules should be eligible (Internet + Mobile bundle)
    assert len(eligible) == 2
    assert eligible[0].name == "Avantage multi-produits Internet"


def test_promotion_eligibility(bundle_context, sample_promotions):
    """Test finding eligible promotions"""
    calculator = PricingCalculator(bundle_context, [], sample_promotions)
    
    eligible = calculator._find_eligible_promotions()
    
    # Promotion should be eligible (has Mobile product)
    assert len(eligible) == 1
    assert eligible[0].name == "Promo: -15€ pendant 6 mois"


def test_complete_calculation(bundle_context, sample_price_rules, sample_promotions):
    """Test complete pricing calculation"""
    result = calculate_bundle_pricing(bundle_context, sample_price_rules, sample_promotions)
    
    # Verify base price
    assert result.base_monthly_total == Decimal("81.00")
    
    # Verify discounts applied
    # Should have 2 price rules (€4 + €5 = €9)
    assert result.permanent_discount_total == Decimal("9.00")
    
    # Should have 1 promotion (€15)
    assert result.promotion_discount_total == Decimal("15.00")
    
    # Verify timeline
    assert len(result.monthly_breakdown) == 12
    
    # Month 1: Base (81) - Permanent (9) - Promo (15) + Fees (39) = 96
    month_1 = result.monthly_breakdown[0]
    assert month_1.base_price == Decimal("81.00")
    assert month_1.permanent_discounts == Decimal("9.00")
    assert month_1.temporary_discounts == Decimal("15.00")
    assert month_1.one_time_fees == Decimal("39.00")
    # Total due = 81 - 9 - 15 + 39 = 96
    assert month_1.total_due == Decimal("96.00")
    
    # Month 2-6: Base (81) - Permanent (9) - Promo (15) = 57
    month_2 = result.monthly_breakdown[1]
    assert month_2.total_monthly == Decimal("57.00")
    assert month_2.one_time_fees == Decimal("0")
    
    # Month 7-12: Base (81) - Permanent (9) = 72 (promo expired)
    month_7 = result.monthly_breakdown[6]
    assert month_7.total_monthly == Decimal("72.00")
    assert month_7.temporary_discounts == Decimal("0")
    
    # Verify summary
    assert result.summary.first_month_total == Decimal("96.00")
    assert result.summary.promotional_period_monthly == Decimal("57.00")
    assert result.summary.promotional_period_months == 6
    assert result.summary.permanent_monthly == Decimal("72.00")


def test_calculation_with_options(sample_products, sample_options, sample_price_rules):
    """Test calculation with options added"""
    context = BundleContext(
        products=sample_products,
        options=sample_options,  # Add Netflix
        product_ids=["54801", "54831"],
        option_ids=["54891"],
        group_ids=["54776", "54781"],
        calculation_date=datetime(2025, 10, 27),
        duration_months=12
    )
    
    result = calculate_bundle_pricing(context, sample_price_rules, [])
    
    # Base = Internet (59) + Mobile (22) + Netflix (14.99) = 95.99
    assert result.base_monthly_total == Decimal("95.99")


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

def test_no_eligible_promotions(bundle_context, sample_price_rules):
    """Test calculation when no promotions are eligible"""
    # Promotion with impossible rule
    bad_promo = PromotionBase(
        id="BAD",
        name="Impossible Promo",
        promo_type=PromoType.DISCOUNT,
        calculation_method=CalculationMethod.AMOUNT,
        calculation_value=Decimal("20.00"),
        duration_months=6,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 12, 31),
        rules=[
            Rule(type=RuleType.HAS_PRODUCT, parameters=["99999"])  # Non-existent product
        ],
        excluded_promos=[]
    )
    
    result = calculate_bundle_pricing(bundle_context, sample_price_rules, [bad_promo])
    
    # Should have no promotion discount
    assert result.promotion_discount_total == Decimal("0")
    assert len(result.applied_promotions) == 0


def test_expired_promotion(bundle_context, sample_price_rules):
    """Test that expired promotions are not applied"""
    expired_promo = PromotionBase(
        id="EXPIRED",
        name="Expired Promo",
        promo_type=PromoType.DISCOUNT,
        calculation_method=CalculationMethod.AMOUNT,
        calculation_value=Decimal("20.00"),
        duration_months=6,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 6, 30),  # Already expired
        rules=[],
        excluded_promos=[]
    )
    
    result = calculate_bundle_pricing(bundle_context, sample_price_rules, [expired_promo])
    
    # Should not apply expired promotion
    assert result.promotion_discount_total == Decimal("0")


def test_promotion_exclusion():
    """Test that excluded promotions don't stack"""
    # Create test context
    products = [
        ProductDetail(
            id="54801",
            display_name="Internet 500",
            slug="net",
            group_id="54776",
            monthly_price=Decimal("59"),
            activation_fee=Decimal("0"),
            specs={}
        )
    ]
    
    context = BundleContext(
        products=products,
        options=[],
        product_ids=["54801"],
        option_ids=[],
        group_ids=["54776"],
        calculation_date=datetime(2025, 10, 27),
        duration_months=12
    )
    
    # Two promotions that exclude each other
    promo_a = PromotionBase(
        id="PROMO_A",
        name="Promo A",
        promo_type=PromoType.DISCOUNT,
        calculation_method=CalculationMethod.AMOUNT,
        calculation_value=Decimal("10"),
        duration_months=6,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 12, 31),
        rules=[],
        excluded_promos=["PROMO_B"],
        calculation_order=10
    )
    
    promo_b = PromotionBase(
        id="PROMO_B",
        name="Promo B",
        promo_type=PromoType.DISCOUNT,
        calculation_method=CalculationMethod.AMOUNT,
        calculation_value=Decimal("15"),
        duration_months=6,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 12, 31),
        rules=[],
        excluded_promos=[],
        calculation_order=20
    )
    
    result = calculate_bundle_pricing(context, [], [promo_a, promo_b])
    
    # Should only apply one promotion (A wins due to better calculationOrder)
    assert len(result.applied_promotions) <= 1


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
