# AI Agent Search Endpoint Guide

## Overview

The `/search` endpoint is a unified, intelligent search API designed specifically for AI agents to discover and recommend Orange Belgium subscription bundles for users.

## Endpoint

```
POST /search
Content-Type: application/json
```

## Key Features

✅ **Natural Language Support** - Accept free-form user queries  
✅ **Intelligent Ranking** - Results sorted by relevance (0-100 score)  
✅ **Bundle Generation** - Automatically creates and prices bundles  
✅ **Promotional Pricing** - Includes all active discounts and savings  
✅ **Explainable Results** - Each result includes "match_reasons"  
✅ **Top Recommendations** - Top 3 results marked as recommended  

---

## Request Format

### Minimal Request (Natural Language)

```json
{
  "query": "cheapest internet for family"
}
```

### Structured Request

```json
{
  "budget_max": 80,
  "include_internet": true,
  "include_mobile": true,
  "family_size": 4,
  "limit": 5
}
```

### Combined Request

```json
{
  "query": "fast internet with Netflix",
  "budget_max": 100,
  "internet_speed_min": 500,
  "include_netflix": true,
  "limit": 10
}
```

---

## Request Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `query` | string | Natural language query | "cheapest bundle with TV" |
| `budget_max` | float | Maximum monthly price (€) | 80.0 |
| `budget_min` | float | Minimum monthly price (€) | 30.0 |
| `internet_speed_min` | int | Min speed (Mbps) | 500 |
| `mobile_data_min` | int | Min data (GB) | 60 |
| `include_tv` | bool | Must include TV | true |
| `include_mobile` | bool | Must include mobile | true |
| `include_internet` | bool | Must include internet | true |
| `family_size` | int | Number of people | 4 |
| `include_netflix` | bool | Must include Netflix | true |
| `include_sports` | bool | Must include sports | true |
| `limit` | int | Max results (default: 10) | 5 |

---

## Response Format

```json
{
  "results": [
    {
      "result_id": "54806-54831",
      "result_type": "bundle",
      "name": "Giga + Medium Bundle",
      "description": "Complete package: Internet illimité 1000 Mbps, Mobile Medium",
      "monthly_price": 77.0,
      "relevance_score": 90.0,
      "match_reasons": [
        "Complete bundle package",
        "Internet + Mobile (Love bundle)",
        "€14 monthly savings"
      ],
      "recommended": true,
      "bundle_details": {
        "base_price": 91.0,
        "discounts": 14.0,
        "final_price": 77.0
      },
      "promotional_savings": 14.0,
      "products": [
        {
          "id": "54806",
          "name": "Internet illimité 1000 Mbps",
          "monthly_price": 69.0,
          "group_id": "54776"
        },
        {
          "id": "54831",
          "name": "Mobile Medium",
          "monthly_price": 22.0,
          "group_id": "54781"
        }
      ]
    }
  ],
  "total_found": 8,
  "search_criteria": {
    "budget_max": 100,
    "include_internet": true,
    "include_mobile": true
  },
  "recommendations": [
    /* Top 3 results with recommended: true */
  ]
}
```

---

## Natural Language Query Examples

### 1. Budget-Focused

```json
{
  "query": "cheapest internet plan"
}
```

**AI Agent Use Case:** User asks "What's the cheapest internet you have?"

### 2. Feature-Focused

```json
{
  "query": "fast internet with sports channels"
}
```

**AI Agent Use Case:** User says "I want fast internet to watch football"

### 3. Family-Focused

```json
{
  "query": "family bundle with Netflix"
}
```

**AI Agent Use Case:** User says "I need internet, mobile, and Netflix for my family"

### 4. Speed-Focused

```json
{
  "query": "1000 Mbps internet"
}
```

**AI Agent Use Case:** User says "I need gigabit internet"

---

## Structured Query Examples

### Example 1: Budget-Constrained Family

**User Need:** Family of 4 needs internet and mobile under €90/month

```json
{
  "budget_max": 90,
  "include_internet": true,
  "include_mobile": true,
  "family_size": 4
}
```

### Example 2: Speed Requirement

**User Need:** Fast internet (at least 500 Mbps) under €70

```json
{
  "budget_max": 70,
  "internet_speed_min": 500,
  "include_internet": true
}
```

### Example 3: Complete Package

**User Need:** Everything (Internet + Mobile + TV + Netflix)

```json
{
  "include_internet": true,
  "include_mobile": true,
  "include_tv": true,
  "include_netflix": true,
  "budget_max": 120
}
```

### Example 4: Mobile-Only

**User Need:** Mobile plan with at least 60GB data

```json
{
  "include_mobile": true,
  "mobile_data_min": 60
}
```

---

## AI Agent Integration Guide

### Step 1: Parse User Intent

```python
def parse_user_request(user_message: str) -> dict:
    """Convert natural language to search request"""
    
    search_request = {}
    
    # Extract budget
    if "under" in user_message or "maximum" in user_message:
        # Extract number
        search_request["budget_max"] = extract_budget(user_message)
    
    # Extract requirements
    if "internet" in user_message:
        search_request["include_internet"] = True
    if "mobile" in user_message or "phone" in user_message:
        search_request["include_mobile"] = True
    if "tv" in user_message or "television" in user_message:
        search_request["include_tv"] = True
    if "netflix" in user_message.lower():
        search_request["include_netflix"] = True
    
    # Extract family size
    if "family" in user_message:
        search_request["family_size"] = 4
    
    # Always include the original query for better matching
    search_request["query"] = user_message
    
    return search_request
```

### Step 2: Call API

```python
import requests

def search_subscriptions(user_message: str):
    # Parse user intent
    search_request = parse_user_request(user_message)
    
    # Call API
    response = requests.post(
        "https://your-api.com/search",
        json=search_request
    )
    
    return response.json()
```

### Step 3: Present Results

```python
def format_results_for_user(search_response: dict) -> str:
    """Format API response for user"""
    
    recommendations = search_response["recommendations"]
    
    if not recommendations:
        return "Sorry, I couldn't find any plans matching your criteria."
    
    message = "Here are my top recommendations:\n\n"
    
    for i, result in enumerate(recommendations, 1):
        message += f"{i}. **{result['name']}** - €{result['monthly_price']}/month\n"
        message += f"   {result['description']}\n"
        
        # Show savings if available
        if result.get('promotional_savings'):
            message += f"   💰 Save €{result['promotional_savings']}/month\n"
        
        # Show why it matches
        message += f"   ✓ {', '.join(result['match_reasons'])}\n\n"
    
    return message
```

---

## Result Types

### 1. Product Results

Single products (Internet, Mobile, or TV)

```json
{
  "result_type": "product",
  "name": "Internet illimité 500 Mbps",
  "products": [/* single product */]
}
```

### 2. Bundle Results

Multiple products combined with pricing

```json
{
  "result_type": "bundle",
  "name": "Zen + Medium Bundle",
  "products": [/* 2-3 products */],
  "bundle_details": {
    "base_price": 81.0,
    "discounts": 9.0,
    "final_price": 72.0
  }
}
```

### 3. Option Results

Add-on services (Netflix, Sports, etc.)

```json
{
  "result_type": "option",
  "name": "Netflix",
  "options": [/* single option */]
}
```

---

## Relevance Scoring

Results are scored 0-100 based on:

- **Budget Match** (Hard filter - excludes results outside budget)
- **Feature Match** (+20-30 points per matching requirement)
- **Query Match** (+10-15 points for keyword matches)
- **Bundle Bonus** (+20 points for complete bundles)
- **Discount Bonus** (+10 points for promotional savings)
- **Family Size Match** (+15 points for appropriate size)

**Recommended Results:** Top 3 results (score typically 70-100)

---

## Common Use Cases

### Use Case 1: Discovery

**User:** "What internet plans do you have?"

```json
{
  "query": "internet plans",
  "include_internet": true
}
```

### Use Case 2: Comparison

**User:** "Compare your mobile plans"

```json
{
  "query": "compare mobile",
  "include_mobile": true,
  "limit": 5
}
```

### Use Case 3: Budget Planning

**User:** "What can I get for 50 euros?"

```json
{
  "budget_max": 50,
  "query": "what can I get for 50 euros"
}
```

### Use Case 4: Upgrade Recommendation

**User:** "I have Start Fiber, what's better?"

```json
{
  "query": "better than Start Fiber",
  "internet_speed_min": 500,
  "include_internet": true
}
```

### Use Case 5: Family Package

**User:** "My family of 5 needs everything"

```json
{
  "family_size": 5,
  "include_internet": true,
  "include_mobile": true,
  "include_tv": true
}
```

---

## Error Handling

### Empty Results

```json
{
  "results": [],
  "total_found": 0,
  "recommendations": []
}
```

**AI Agent Response:** "I couldn't find any plans matching those criteria. Would you like to adjust your budget or requirements?"

### API Error

```json
{
  "detail": "Search failed: [error message]"
}
```

**AI Agent Response:** "I'm having trouble searching right now. Please try again in a moment."

---

## Best Practices for AI Agents

### 1. Always Include Context

```json
{
  "query": "fast internet",  // Include original user message
  "internet_speed_min": 500  // Plus extracted criteria
}
```

### 2. Use Recommendations First

```python
# Present the top 3 recommendations
recommendations = response["recommendations"]
```

### 3. Explain Match Reasons

```python
for reason in result["match_reasons"]:
    print(f"✓ {reason}")
```

### 4. Highlight Savings

```python
if result["promotional_savings"]:
    print(f"💰 Save €{result['promotional_savings']}/month!")
```

### 5. Handle Edge Cases

```python
if response["total_found"] == 0:
    suggest_alternative_criteria()
```

---

## Testing Queries

Test these queries to verify the endpoint works:

```bash
# Test 1: Simple query
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "cheapest internet"}'

# Test 2: Budget search
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"budget_max": 60, "include_internet": true}'

# Test 3: Family bundle
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"family_size": 4, "include_mobile": true, "include_tv": true}'
```

---

## Advanced Features

### 1. Multi-Mobile Bundles

The search automatically considers bundles with multiple mobile plans for families:

```json
{
  "family_size": 4,
  "include_mobile": true
}
```

Returns bundles like: Internet + 2-4 Mobile plans

### 2. Netflix Variants

When `include_netflix: true`, considers both:
- Internet plans with Netflix included
- Netflix as an add-on option

### 3. Speed Optimization

Automatically maps common terms:
- "fast" → 500+ Mbps
- "giga" / "1000" → 1000 Mbps
- "basic" / "cheap" → 200 Mbps

---

## Support

For questions or issues with the `/search` endpoint:
- Check the interactive docs at `/docs`
- Review example queries in this guide
- Test with simple queries first, then add complexity

**Happy Searching! 🔍**

