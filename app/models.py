"""
Pydantic Models for Orange Belgium API
======================================
Type-safe models for requests, responses, and internal data structures
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class CalculationMethod(str, Enum):
    """How discounts are calculated"""
    AMOUNT = "amount"  # Fixed euro amount
    PERCENTAGE = "percentage"  # Percentage of price
    FREE = "free"  # Completely free


class PromoType(str, Enum):
    """Type of promotion"""
    DISCOUNT = "discount"
    ACTIVATION_FEE = "activationFee"
    DATA = "data"


class RuleType(str, Enum):
    """Types of rules for eligibility checking"""
    HAS_PRODUCT = "hasProduct"
    HAS_PRODUCT_IN_GROUP = "hasProductInGroup"
    HAS_ONLY_PRODUCT_IN_GROUP = "hasOnlyProductInGroup"
    HAS_OPTION = "hasOption"
    ITEM_NUMBER = "itemNumber"
    ITEM_MIN = "itemMin"


# ============================================================================
# BASE MODELS
# ============================================================================

class PriceComponent(BaseModel):
    """Price breakdown component"""
    monthly_price: Decimal = Field(default=0, description="Monthly recurring cost")
    device_fee: Decimal = Field(default=0, description="Device/equipment cost")
    activation_fee: Decimal = Field(default=0, description="One-time activation fee")
    installation_fee: Decimal = Field(default=0, description="One-time installation fee")


class Rule(BaseModel):
    """Eligibility rule for price rules and promotions"""
    type: RuleType = Field(..., description="Type of rule to evaluate")
    parameters: List[str] = Field(default_factory=list, description="Rule parameters (product IDs, etc.)")


# ============================================================================
# PRODUCT MODELS
# ============================================================================

class GroupBase(BaseModel):
    """Product group (Internet, Mobile, TV, Extra)"""
    id: str
    name: str
    slug: str


class ProductBase(BaseModel):
    """Base product information"""
    id: str
    display_name: str
    slug: str
    group_id: str
    monthly_price: Decimal
    activation_fee: Decimal = 0
    specs: Dict[str, Any] = Field(default_factory=dict)


class ProductDetail(ProductBase):
    """Detailed product information"""
    internal_name: Optional[str] = None
    epc_id: Optional[str] = None
    device_fee: Decimal = 0
    installation_fee: Decimal = 0
    description: Optional[str] = None
    card_title: Optional[str] = None
    card_subtitle: Optional[str] = None
    group_name: Optional[str] = None


class OptionBase(BaseModel):
    """Add-on option (Netflix, WiFi Comfort, etc.)"""
    id: str
    name: str
    monthly_price: Decimal
    option_type: Optional[str] = None
    description: Optional[str] = None


# ============================================================================
# PRICING MODELS
# ============================================================================

class PriceRuleBase(BaseModel):
    """Permanent bundle discount"""
    id: str
    name: str
    calculation_method: CalculationMethod
    calculation_value: Decimal
    rules: List[Rule] = Field(default_factory=list)


class PromotionBase(BaseModel):
    """Time-limited promotional offer"""
    id: str
    name: str
    promo_type: PromoType
    calculation_method: CalculationMethod
    calculation_value: Decimal
    duration_months: int
    start_date: datetime
    end_date: datetime
    rules: List[Rule] = Field(default_factory=list)
    excluded_promos: List[str] = Field(default_factory=list)
    legal_summary: Optional[str] = None


class AppliedDiscount(BaseModel):
    """A discount that has been applied to the bundle"""
    id: str
    name: str
    type: str = Field(..., description="'price_rule' or 'promotion'")
    discount_amount: Decimal
    duration_months: Optional[int] = None  # None = permanent
    applies_to_product: Optional[str] = None  # Which product gets the discount


# ============================================================================
# CALCULATION MODELS
# ============================================================================

class MonthlyBreakdown(BaseModel):
    """Cost breakdown for a specific month"""
    month: int = Field(..., description="Month number (1-based)")
    base_price: Decimal = Field(..., description="Sum of all product base prices")
    permanent_discounts: Decimal = Field(default=0, description="Bundle discounts (Avantage à vie)")
    temporary_discounts: Decimal = Field(default=0, description="Time-limited promotions")
    total_monthly: Decimal = Field(..., description="Total monthly cost")
    one_time_fees: Decimal = Field(default=0, description="Activation/installation fees")
    total_due: Decimal = Field(..., description="Total amount due this month")


class PricingSummary(BaseModel):
    """Summary of costs over time"""
    first_month_total: Decimal = Field(..., description="Total for first month (including fees)")
    promotional_period_monthly: Decimal = Field(..., description="Monthly cost during promotions")
    promotional_period_months: int = Field(..., description="How many months promotions last")
    permanent_monthly: Decimal = Field(..., description="Monthly cost after promotions end")
    first_year_total: Decimal = Field(..., description="Total cost for first 12 months")
    second_year_total: Decimal = Field(..., description="Total cost for second year")


class BundleCalculation(BaseModel):
    """Complete bundle pricing calculation"""
    products: List[ProductBase]
    options: List[OptionBase] = Field(default_factory=list)
    base_monthly_total: Decimal
    permanent_discount_total: Decimal
    promotion_discount_total: Decimal
    
    applied_price_rules: List[AppliedDiscount] = Field(default_factory=list)
    applied_promotions: List[AppliedDiscount] = Field(default_factory=list)
    
    monthly_breakdown: List[MonthlyBreakdown]
    summary: PricingSummary
    
    is_valid_bundle: bool = True
    validation_message: Optional[str] = None


# ============================================================================
# REQUEST MODELS
# ============================================================================

class ProductSearchRequest(BaseModel):
    """Search for products by criteria"""
    group: Optional[str] = Field(None, description="Group slug: internet, mobile, tv")
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    keyword: Optional[str] = Field(None, description="Search in product name")
    specs: Optional[Dict[str, Any]] = Field(None, description="Filter by specs (e.g., speed >= 500)")


class BundleCalculationRequest(BaseModel):
    """Request to calculate bundle pricing"""
    product_ids: List[str] = Field(..., min_items=1, description="List of product IDs to bundle")
    option_ids: List[str] = Field(default_factory=list, description="List of option IDs to add")
    calculation_date: Optional[datetime] = Field(None, description="Date for promotion filtering (default: today)")
    duration_months: int = Field(12, ge=1, le=60, description="Calculate costs for this many months")
    
    @validator('calculation_date', pre=True, always=True)
    def set_default_date(cls, v):
        return v or datetime.now()


class BundleValidationRequest(BaseModel):
    """Check if products can be bundled together"""
    product_ids: List[str] = Field(..., min_items=1)
    option_ids: List[str] = Field(default_factory=list)


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class ProductSearchResponse(BaseModel):
    """Response for product search"""
    products: List[ProductDetail]
    total_count: int
    filters_applied: Dict[str, Any]


class BundleValidationResponse(BaseModel):
    """Response for bundle validation"""
    is_valid: bool
    message: str
    compatible_products: List[str] = Field(default_factory=list)
    incompatible_products: List[str] = Field(default_factory=list)
    configurator_used: Optional[str] = None


class PromotionListResponse(BaseModel):
    """Response for active promotions"""
    promotions: List[PromotionBase]
    total_count: int
    as_of_date: datetime


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================================
# INTERNAL MODELS
# ============================================================================

class BundleContext(BaseModel):
    """Internal context for bundle calculation"""
    products: List[ProductDetail]
    options: List[OptionBase]
    product_ids: List[str]
    option_ids: List[str]
    group_ids: List[str]  # Groups represented in the bundle
    calculation_date: datetime
    duration_months: int


class EligibilityCheck(BaseModel):
    """Result of checking if a rule/promo is eligible"""
    is_eligible: bool
    reason: Optional[str] = None


# ============================================================================
# SEARCH MODELS
# ============================================================================

class SearchRequest(BaseModel):
    """Request model for intelligent search endpoint"""
    query: Optional[str] = Field(None, description="Natural language query (e.g., 'cheapest internet for family')")
    budget_max: Optional[float] = Field(None, description="Maximum monthly budget in euros")
    budget_min: Optional[float] = Field(None, description="Minimum monthly budget in euros")
    internet_speed_min: Optional[int] = Field(None, description="Minimum internet speed in Mbps")
    mobile_data_min: Optional[int] = Field(None, description="Minimum mobile data in GB")
    include_tv: Optional[bool] = Field(None, description="Must include TV service")
    include_mobile: Optional[bool] = Field(None, description="Must include mobile service")
    include_internet: Optional[bool] = Field(None, description="Must include internet service")
    family_size: Optional[int] = Field(None, description="Number of people in household")
    include_netflix: Optional[bool] = Field(None, description="Must include Netflix")
    include_sports: Optional[bool] = Field(None, description="Must include sports channels")
    limit: int = Field(10, description="Maximum number of results to return")


class SearchResultItem(BaseModel):
    """A single search result"""
    result_id: str = Field(..., description="Unique identifier for this result")
    result_type: str = Field(..., description="Type: 'product', 'bundle', or 'option'")
    name: str = Field(..., description="Name of the product/bundle")
    description: str = Field(..., description="Description")
    monthly_price: Decimal = Field(..., description="Total monthly price")
    relevance_score: float = Field(..., description="Relevance score (0-100)")
    match_reasons: List[str] = Field(..., description="Why this result matches the search")
    products: Optional[List[ProductDetail]] = Field(None, description="Products included")
    options: Optional[List[OptionBase]] = Field(None, description="Options included")
    bundle_details: Optional[Dict[str, Any]] = Field(None, description="Bundle pricing breakdown")
    promotional_savings: Optional[Decimal] = Field(None, description="Monthly promotional savings")
    recommended: bool = Field(False, description="Whether this is a top recommendation")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class SearchResponse(BaseModel):
    """Response from search endpoint"""
    results: List[SearchResultItem] = Field(..., description="Search results ranked by relevance")
    total_found: int = Field(..., description="Total number of results found")
    search_criteria: Dict[str, Any] = Field(..., description="Applied search criteria")
    recommendations: List[SearchResultItem] = Field(..., description="Top 3 recommendations")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Pydantic configuration"""
    json_encoders = {
        Decimal: lambda v: float(v),
        datetime: lambda v: v.isoformat()
    }
    use_enum_values = True
