"""
Orange Belgium Search Engine
=============================
Intelligent search and recommendation system for AI agents.
Searches across products, bundles, and options with natural language support.
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime

from app.database import OrangeDatabase
from app.models import ProductDetail, OptionBase, BundleContext
from app.calculator import calculate_bundle_pricing


@dataclass
class SearchCriteria:
    """Search criteria for finding products/bundles"""
    query: Optional[str] = None
    budget_max: Optional[Decimal] = None
    budget_min: Optional[Decimal] = None
    internet_speed_min: Optional[int] = None  # Mbps
    mobile_data_min: Optional[int] = None  # GB
    include_tv: Optional[bool] = None
    include_mobile: Optional[bool] = None
    include_internet: Optional[bool] = None
    family_size: Optional[int] = None  # Number of people
    include_netflix: Optional[bool] = None
    include_sports: Optional[bool] = None
    must_have_products: Optional[List[str]] = None
    exclude_products: Optional[List[str]] = None
    

@dataclass
class SearchResult:
    """A single search result with relevance score"""
    result_id: str
    result_type: str  # 'product', 'bundle', 'option'
    name: str
    description: str
    monthly_price: Decimal
    relevance_score: float  # 0-100
    match_reasons: List[str]
    products: Optional[List[ProductDetail]] = None
    options: Optional[List[OptionBase]] = None
    bundle_details: Optional[Dict[str, Any]] = None
    promotional_savings: Optional[Decimal] = None
    recommended: bool = False


class SearchEngine:
    """
    Intelligent search engine for Orange Belgium products and bundles.
    Designed to be easily queryable by AI agents.
    """
    
    def __init__(self, db: OrangeDatabase):
        self.db = db
        
    def search(
        self,
        query: Optional[str] = None,
        budget_max: Optional[float] = None,
        budget_min: Optional[float] = None,
        internet_speed_min: Optional[int] = None,
        mobile_data_min: Optional[int] = None,
        include_tv: Optional[bool] = None,
        include_mobile: Optional[bool] = None,
        include_internet: Optional[bool] = None,
        family_size: Optional[int] = None,
        include_netflix: Optional[bool] = None,
        include_sports: Optional[bool] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """
        Search for products, bundles, and options based on criteria.
        
        Args:
            query: Natural language query (e.g., "cheapest internet", "family bundle with Netflix")
            budget_max: Maximum monthly budget
            budget_min: Minimum monthly budget
            internet_speed_min: Minimum internet speed in Mbps
            mobile_data_min: Minimum mobile data in GB
            include_tv: Must include TV
            include_mobile: Must include mobile
            include_internet: Must include internet
            family_size: Number of people (helps recommend plans)
            include_netflix: Must include Netflix
            include_sports: Must include sports channels
            limit: Maximum number of results
            
        Returns:
            List of SearchResult objects ranked by relevance
        """
        results = []
        
        # Parse query for keywords if provided
        keywords = self._extract_keywords(query) if query else {}
        
        # Build search criteria
        criteria = SearchCriteria(
            query=query,
            budget_max=Decimal(str(budget_max)) if budget_max else None,
            budget_min=Decimal(str(budget_min)) if budget_min else None,
            internet_speed_min=internet_speed_min or keywords.get('internet_speed'),
            mobile_data_min=mobile_data_min or keywords.get('mobile_data'),
            include_tv=include_tv if include_tv is not None else keywords.get('tv'),
            include_mobile=include_mobile if include_mobile is not None else keywords.get('mobile'),
            include_internet=include_internet if include_internet is not None else keywords.get('internet'),
            family_size=family_size or keywords.get('family_size'),
            include_netflix=include_netflix if include_netflix is not None else keywords.get('netflix'),
            include_sports=include_sports if include_sports is not None else keywords.get('sports')
        )
        
        # Search products
        product_results = self._search_products(criteria)
        results.extend(product_results)
        
        # Search bundles (combinations of products)
        bundle_results = self._search_bundles(criteria)
        results.extend(bundle_results)
        
        # Search options if specifically requested
        if criteria.include_netflix or criteria.include_sports or \
           (query and ('option' in query.lower() or 'add-on' in query.lower())):
            option_results = self._search_options(criteria)
            results.extend(option_results)
        
        # Sort by relevance score
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Mark top 3 as recommended
        for i, result in enumerate(results[:3]):
            result.recommended = True
        
        return results[:limit]
    
    def _extract_keywords(self, query: str) -> Dict[str, Any]:
        """Extract structured data from natural language query"""
        query_lower = query.lower()
        keywords = {}
        
        # Internet speed keywords
        if 'giga' in query_lower or '1000' in query_lower or '1 gbps' in query_lower:
            keywords['internet_speed'] = 1000
        elif '500' in query_lower:
            keywords['internet_speed'] = 500
        elif '200' in query_lower:
            keywords['internet_speed'] = 200
        elif 'fast' in query_lower or 'high speed' in query_lower:
            keywords['internet_speed'] = 500
        elif 'basic' in query_lower or 'cheap' in query_lower:
            keywords['internet_speed'] = 200
            
        # Mobile data keywords
        if 'unlimited' in query_lower and 'mobile' in query_lower:
            keywords['mobile_data'] = 300  # Large plan
        elif 'large' in query_lower and 'mobile' in query_lower:
            keywords['mobile_data'] = 60
        elif 'medium' in query_lower and 'mobile' in query_lower:
            keywords['mobile_data'] = 20
        elif 'small' in query_lower and 'mobile' in query_lower:
            keywords['mobile_data'] = 10
            
        # Product type keywords
        keywords['internet'] = any(word in query_lower for word in ['internet', 'wifi', 'broadband', 'fiber'])
        keywords['mobile'] = any(word in query_lower for word in ['mobile', 'phone', 'gsm', 'sim'])
        keywords['tv'] = any(word in query_lower for word in ['tv', 'television', 'channels'])
        
        # Feature keywords
        keywords['netflix'] = 'netflix' in query_lower
        keywords['sports'] = any(word in query_lower for word in ['sport', 'football', 'soccer'])
        
        # Family size
        if 'family' in query_lower:
            keywords['family_size'] = 4
        elif 'couple' in query_lower:
            keywords['family_size'] = 2
        elif 'single' in query_lower:
            keywords['family_size'] = 1
            
        return keywords
    
    def _search_products(self, criteria: SearchCriteria) -> List[SearchResult]:
        """Search individual products"""
        results = []
        all_products = self.db.get_products()
        
        for product in all_products:
            score = 0
            reasons = []
            
            # Budget filtering (hard filter)
            if criteria.budget_max and product.monthly_price > criteria.budget_max:
                continue
            if criteria.budget_min and product.monthly_price < criteria.budget_min:
                continue
            
            # Group filtering
            product_group = self._get_product_group(product.group_id)
            if product_group:
                group_slug = product_group.slug
                
                # Hard filters for required product types
                if criteria.include_internet and group_slug != 'internet':
                    continue
                if criteria.include_mobile and group_slug != 'mobile':
                    continue
                if criteria.include_tv and group_slug != 'tv':
                    continue
                
                # Score matching
                if group_slug == 'internet':
                    score += 30
                    reasons.append("Internet product")
                    
                    # Speed matching
                    if criteria.internet_speed_min:
                        speed = self._extract_speed_from_name(product.name)
                        if speed and speed >= criteria.internet_speed_min:
                            score += 20
                            reasons.append(f"Meets speed requirement ({speed} Mbps)")
                        elif speed:
                            score -= 10
                            
                elif group_slug == 'mobile':
                    score += 30
                    reasons.append("Mobile product")
                    
                    # Data matching
                    if criteria.mobile_data_min:
                        data = self._extract_data_from_name(product.name)
                        if data and data >= criteria.mobile_data_min:
                            score += 20
                            reasons.append(f"Meets data requirement ({data} GB)")
                            
                elif group_slug == 'tv':
                    score += 30
                    reasons.append("TV product")
            
            # Netflix check
            if criteria.include_netflix and 'netflix' in product.name.lower():
                score += 25
                reasons.append("Includes Netflix")
            
            # Query matching
            if criteria.query:
                query_lower = criteria.query.lower()
                if query_lower in product.name.lower():
                    score += 15
                    reasons.append("Name matches query")
                if product.description and query_lower in product.description.lower():
                    score += 10
                    reasons.append("Description matches query")
            
            # Family size recommendations
            if criteria.family_size:
                if criteria.family_size >= 4 and 'large' in product.name.lower():
                    score += 15
                    reasons.append("Suitable for large family")
                elif criteria.family_size <= 2 and 'small' in product.name.lower():
                    score += 15
                    reasons.append("Suitable for small household")
            
            # Only add if score is positive
            if score > 0:
                results.append(SearchResult(
                    result_id=product.id,
                    result_type='product',
                    name=product.name,
                    description=product.description or "",
                    monthly_price=product.monthly_price,
                    relevance_score=score,
                    match_reasons=reasons,
                    products=[product]
                ))
        
        return results
    
    def _search_bundles(self, criteria: SearchCriteria) -> List[SearchResult]:
        """Search for product bundles that match criteria"""
        results = []
        
        # Get all products for bundling
        all_products = self.db.get_products()
        internet_products = [p for p in all_products if self._get_product_group(p.group_id).slug == 'internet']
        mobile_products = [p for p in all_products if self._get_product_group(p.group_id).slug == 'mobile']
        tv_products = [p for p in all_products if self._get_product_group(p.group_id).slug == 'tv']
        
        # Generate smart bundles based on criteria
        bundle_configs = []
        
        # If user wants everything, create Love bundles
        if criteria.include_internet or criteria.include_mobile:
            # Internet + Mobile bundles
            for internet in internet_products[:3]:  # Top 3 internet plans
                for mobile in mobile_products[:3]:  # Top 3 mobile plans
                    # Basic bundle
                    bundle_configs.append([internet.id, mobile.id])
                    
                    # Bundle with TV if requested
                    if criteria.include_tv and tv_products:
                        for tv in tv_products[:2]:
                            bundle_configs.append([internet.id, mobile.id, tv.id])
        
        # For each bundle configuration, calculate pricing and score
        for product_ids in bundle_configs:
            try:
                # Calculate bundle pricing
                context = BundleContext(product_ids=product_ids, option_ids=[])
                pricing = calculate_bundle_pricing(context, self.db)
                
                if not pricing:
                    continue
                
                total_price = pricing.summary.grand_total
                
                # Budget filtering
                if criteria.budget_max and total_price > criteria.budget_max:
                    continue
                if criteria.budget_min and total_price < criteria.budget_min:
                    continue
                
                # Calculate score
                score = 50  # Base score for bundles
                reasons = ["Complete bundle package"]
                
                # Check if bundle matches requirements
                bundle_products = [p for p in all_products if p.id in product_ids]
                has_internet = any(self._get_product_group(p.group_id).slug == 'internet' for p in bundle_products)
                has_mobile = any(self._get_product_group(p.group_id).slug == 'mobile' for p in bundle_products)
                has_tv = any(self._get_product_group(p.group_id).slug == 'tv' for p in bundle_products)
                
                if has_internet and has_mobile:
                    score += 20
                    reasons.append("Internet + Mobile (Love bundle)")
                if has_tv:
                    score += 15
                    reasons.append("Includes TV")
                
                # Check for multi-product discount
                if pricing.summary.total_discounts > 0:
                    score += 10
                    reasons.append(f"€{pricing.summary.total_discounts} monthly savings")
                
                # Create bundle name
                product_names = [p.name for p in bundle_products]
                bundle_name = " + ".join([name.split()[0] for name in product_names[:3]])
                
                results.append(SearchResult(
                    result_id="-".join(product_ids),
                    result_type='bundle',
                    name=f"{bundle_name} Bundle",
                    description=f"Complete package: {', '.join(product_names)}",
                    monthly_price=total_price,
                    relevance_score=score,
                    match_reasons=reasons,
                    products=bundle_products,
                    bundle_details={
                        'base_price': float(pricing.summary.base_monthly_total),
                        'discounts': float(pricing.summary.total_discounts),
                        'final_price': float(total_price)
                    },
                    promotional_savings=pricing.summary.total_discounts
                ))
                
            except Exception as e:
                # Skip bundles that can't be calculated
                continue
        
        return results
    
    def _search_options(self, criteria: SearchCriteria) -> List[SearchResult]:
        """Search add-on options"""
        results = []
        all_options = self.db.get_options()
        
        for option in all_options:
            score = 0
            reasons = []
            
            # Budget filtering
            if criteria.budget_max and option.monthly_price > criteria.budget_max:
                continue
            
            # Netflix check
            if criteria.include_netflix and 'netflix' in option.name.lower():
                score += 50
                reasons.append("Netflix streaming service")
            
            # Sports check
            if criteria.include_sports and 'sport' in option.name.lower():
                score += 50
                reasons.append("Sports channels")
            
            # Query matching
            if criteria.query:
                query_lower = criteria.query.lower()
                if query_lower in option.name.lower():
                    score += 30
                    reasons.append("Matches search query")
            
            if score > 0:
                results.append(SearchResult(
                    result_id=option.id,
                    result_type='option',
                    name=option.name,
                    description=option.description or "",
                    monthly_price=option.monthly_price,
                    relevance_score=score,
                    match_reasons=reasons,
                    options=[option]
                ))
        
        return results
    
    def _get_product_group(self, group_id: str):
        """Get group information by ID"""
        groups = self.db.get_groups()
        return next((g for g in groups if g.id == group_id), None)
    
    def _extract_speed_from_name(self, name: str) -> Optional[int]:
        """Extract internet speed (Mbps) from product name"""
        if '1000' in name or '1 Gbps' in name or 'Giga' in name:
            return 1000
        elif '500' in name:
            return 500
        elif '200' in name:
            return 200
        return None
    
    def _extract_data_from_name(self, name: str) -> Optional[int]:
        """Extract mobile data (GB) from product name"""
        if '300' in name:
            return 300
        elif '60' in name:
            return 60
        elif '10' in name:
            return 10
        elif '2' in name and 'GB' in name:
            return 2
        return None

