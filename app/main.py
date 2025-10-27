"""
Orange Belgium Subscription API
================================
FastAPI application for subscription bundle pricing and recommendations.

Endpoints:
- GET /products - Search products
- GET /options - List available options
- GET /groups - List product groups
- POST /bundles/validate - Check if products can be bundled
- POST /bundles/calculate - Calculate bundle pricing with timeline
- GET /promotions - List active promotions
- GET /health - Health check
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import os
import yaml

from app.models import (
    ProductSearchRequest, ProductSearchResponse,
    BundleCalculationRequest, BundleCalculation,
    BundleValidationRequest, BundleValidationResponse,
    PromotionListResponse, ErrorResponse,
    ProductDetail, OptionBase, GroupBase,
    BundleContext
)
from app.database import OrangeDatabase
from app.calculator import calculate_bundle_pricing


# ============================================================================
# APPLICATION SETUP
# ============================================================================

app = FastAPI(
    title="Orange Belgium Subscription API",
    description="API for subscription bundle pricing, promotions, and recommendations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection string from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/orange_belgium"
)


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_database() -> OrangeDatabase:
    """Get database instance"""
    return OrangeDatabase(DATABASE_URL)


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Orange Belgium Subscription API",
        "version": "1.0.0",
        "endpoints": {
            "products": "/products",
            "options": "/options",
            "groups": "/groups",
            "validate_bundle": "POST /bundles/validate",
            "calculate_bundle": "POST /bundles/calculate",
            "promotions": "/promotions",
            "health": "/health"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json",
            "openapi_yaml": "/openapi.yaml"
        }
    }


@app.get("/openapi.yaml", include_in_schema=False, tags=["Documentation"])
async def get_openapi_yaml():
    """
    Get OpenAPI specification in YAML format.
    
    This endpoint is not included in the OpenAPI schema itself.
    Use this to download the API specification for external tools.
    """
    openapi_schema = app.openapi()
    yaml_content = yaml.dump(openapi_schema, default_flow_style=False, sort_keys=False)
    
    return Response(
        content=yaml_content,
        media_type="application/x-yaml",
        headers={
            "Content-Disposition": "attachment; filename=openapi.yaml"
        }
    )


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    try:
        db = get_database()
        # Try a simple query
        groups = db.get_groups()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "groups_count": len(groups)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


# ----------------------------------------------------------------------------
# PRODUCT ENDPOINTS
# ----------------------------------------------------------------------------

@app.get(
    "/products",
    response_model=ProductSearchResponse,
    tags=["Products"],
    summary="Search products"
)
async def search_products(
    group: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    keyword: Optional[str] = None,
    db: OrangeDatabase = Depends(get_database)
):
    """
    Search for products with optional filters.
    
    - **group**: Filter by group slug (internet, mobile, tv)
    - **min_price**: Minimum monthly price
    - **max_price**: Maximum monthly price
    - **keyword**: Search in product name/description
    
    Returns list of matching products with pricing information.
    """
    try:
        # Convert group slug to ID if needed
        group_id = None
        if group:
            groups = db.get_groups()
            matching_group = next((g for g in groups if g.slug == group), None)
            if matching_group:
                group_id = matching_group.id
        
        # Convert prices to Decimal
        min_price_dec = Decimal(str(min_price)) if min_price is not None else None
        max_price_dec = Decimal(str(max_price)) if max_price is not None else None
        
        products = db.get_products(
            group_id=group_id,
            min_price=min_price_dec,
            max_price=max_price_dec,
            keyword=keyword
        )
        
        return ProductSearchResponse(
            products=products,
            total_count=len(products),
            filters_applied={
                "group": group,
                "min_price": min_price,
                "max_price": max_price,
                "keyword": keyword
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/products/{product_id}",
    response_model=ProductDetail,
    tags=["Products"],
    summary="Get product by ID"
)
async def get_product(
    product_id: str,
    db: OrangeDatabase = Depends(get_database)
):
    """Get detailed information about a specific product."""
    product = db.get_product_by_id(product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    
    return product


# ----------------------------------------------------------------------------
# OPTION ENDPOINTS
# ----------------------------------------------------------------------------

@app.get(
    "/options",
    response_model=List[OptionBase],
    tags=["Options"],
    summary="List available options"
)
async def list_options(db: OrangeDatabase = Depends(get_database)):
    """
    Get all available add-on options (Netflix, WiFi Comfort, etc.).
    
    Returns list of options with pricing.
    """
    try:
        return db.get_options()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/options/compatible",
    response_model=List[OptionBase],
    tags=["Options"],
    summary="Get compatible options for products"
)
async def get_compatible_options(
    product_ids: str,
    db: OrangeDatabase = Depends(get_database)
):
    """
    Get options that are compatible with specific products.
    
    - **product_ids**: Comma-separated list of product IDs
    """
    try:
        ids = [pid.strip() for pid in product_ids.split(',')]
        return db.get_compatible_options(ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------------------------------
# GROUP ENDPOINTS
# ----------------------------------------------------------------------------

@app.get(
    "/groups",
    response_model=List[GroupBase],
    tags=["Groups"],
    summary="List product groups"
)
async def list_groups(db: OrangeDatabase = Depends(get_database)):
    """
    Get all product groups (Internet, Mobile, TV, Extra).
    
    Returns list of groups with IDs and slugs.
    """
    try:
        return db.get_groups()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------------------------------
# BUNDLE ENDPOINTS
# ----------------------------------------------------------------------------

@app.post(
    "/bundles/validate",
    response_model=BundleValidationResponse,
    tags=["Bundles"],
    summary="Validate if products can be bundled"
)
async def validate_bundle(
    request: BundleValidationRequest,
    db: OrangeDatabase = Depends(get_database)
):
    """
    Check if the specified products can be bundled together.
    
    Returns validation result with compatibility information.
    """
    try:
        is_valid, configurator_id = db.can_bundle_products(request.product_ids)
        
        if is_valid:
            return BundleValidationResponse(
                is_valid=True,
                message="Products can be bundled together",
                compatible_products=request.product_ids,
                configurator_used=configurator_id
            )
        else:
            return BundleValidationResponse(
                is_valid=False,
                message="These products cannot be bundled together",
                incompatible_products=request.product_ids
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/bundles/calculate",
    response_model=BundleCalculation,
    tags=["Bundles"],
    summary="Calculate bundle pricing",
    description="""
    Calculate complete pricing for a bundle of products and options.
    
    This endpoint:
    1. Validates the bundle is valid
    2. Applies permanent bundle discounts (Avantage multi-produits)
    3. Applies time-limited promotions
    4. Generates month-by-month cost breakdown
    5. Provides cost summary
    
    Returns detailed pricing information including promotional periods.
    """
)
async def calculate_bundle(
    request: BundleCalculationRequest,
    db: OrangeDatabase = Depends(get_database)
):
    """
    Calculate complete bundle pricing with timeline.
    
    **This is the main endpoint for the chatbot.**
    """
    try:
        # 1. Validate bundle
        is_valid, configurator_id = db.can_bundle_products(request.product_ids)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail="These products cannot be bundled together"
            )
        
        # 2. Get products and options
        products = db.get_products_by_ids(request.product_ids)
        if len(products) != len(request.product_ids):
            missing = set(request.product_ids) - {p.id for p in products}
            raise HTTPException(
                status_code=404,
                detail=f"Products not found: {missing}"
            )
        
        options = db.get_options_by_ids(request.option_ids) if request.option_ids else []
        
        # 3. Build context
        group_ids = list(set(p.group_id for p in products))
        
        context = BundleContext(
            products=products,
            options=options,
            product_ids=request.product_ids,
            option_ids=request.option_ids,
            group_ids=group_ids,
            calculation_date=request.calculation_date,
            duration_months=request.duration_months
        )
        
        # 4. Get price rules and promotions
        price_rules = db.get_price_rules()
        promotions = db.get_active_promotions(request.calculation_date)
        
        # 5. Calculate pricing
        calculation = calculate_bundle_pricing(context, price_rules, promotions)
        
        return calculation
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------------------------------
# PROMOTION ENDPOINTS
# ----------------------------------------------------------------------------

@app.get(
    "/promotions",
    response_model=PromotionListResponse,
    tags=["Promotions"],
    summary="List active promotions"
)
async def list_promotions(
    date: Optional[str] = None,
    db: OrangeDatabase = Depends(get_database)
):
    """
    Get all currently active promotions.
    
    - **date**: Check promotions for specific date (YYYY-MM-DD), default: today
    
    Returns list of active time-limited promotions.
    """
    try:
        # Parse date if provided
        if date:
            as_of_date = datetime.fromisoformat(date)
        else:
            as_of_date = datetime.now()
        
        promotions = db.get_active_promotions(as_of_date)
        
        return PromotionListResponse(
            promotions=promotions,
            total_count=len(promotions),
            as_of_date=as_of_date
        )
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return ErrorResponse(
        error="Internal Server Error",
        detail=str(exc),
        timestamp=datetime.now()
    )


# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    print("🚀 Orange Belgium API starting...")
    print(f"   Database: {DATABASE_URL}")
    print(f"   Docs: http://localhost:8000/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Orange Belgium API shutting down...")


# ============================================================================
# DEV/DEBUG ENDPOINTS (remove in production)
# ============================================================================

if os.getenv("ENVIRONMENT") == "development":
    
    @app.get("/debug/stats", tags=["Debug"])
    async def debug_stats(db: OrangeDatabase = Depends(get_database)):
        """Get database statistics (dev only)"""
        return {
            "products": len(db.get_products()),
            "options": len(db.get_options()),
            "groups": len(db.get_groups()),
            "price_rules": len(db.get_price_rules()),
            "promotions": len(db.get_active_promotions())
        }
