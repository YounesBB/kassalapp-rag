import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

KASSALAPP_API_KEY = os.getenv("KASSALAPP_API_KEY")
BASE_URL = "https://kassal.app/api/v1"

if not KASSALAPP_API_KEY:
    raise ValueError("KASSALAPP_API_KEY not found in environment variables")

HEADERS = {
    "Authorization": f"Bearer {KASSALAPP_API_KEY}",
    "Accept": "application/json"
}

def search_products(search: str = None, size: int = 10, sort: str = "price_asc", store: str = None, **kwargs):
    """
    Search for products based on a keyword.
    
    Args:
        search: Search for products based on a keyword (minimum 3 characters).
        size: The number of products to be displayed per page (1-100).
        sort: Sort criteria: price_asc, price_desc, name_asc, name_desc, etc.
        store: Filter products by store (e.g., SPAR_NO, MENY_NO, KIWI).
    """
    # Defensive handling for common LLM parameter hallucinations
    query = search or kwargs.get("search_query") or kwargs.get("query")
    if not query or len(query) < 3:
        return {"error": "Invalid search", "message": "Search must be at least 3 characters."}

    url = f"{BASE_URL}/products"
    params = {
        "search": query,
        "size": size,
        "sort": sort
    }
    if store:
        params["store"] = store
        
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Optimization: Filter response to save tokens
        if "data" in data:
            optimized_data = []
            for p in data["data"]:
                optimized_data.append({
                    "name": p.get("name"),
                    "brand": p.get("brand"),
                    "price": p.get("current_price"),
                    "store": p.get("store", {}).get("name") if p.get("store") else None,
                    "ean": p.get("ean")
                })
            return {"data": optimized_data}
        return data
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "message": "Failed to fetch products"}

def get_product_by_id(product: int):
    """Lookup product by ID."""
    url = f"{BASE_URL}/products/id/{product}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "message": f"Failed to fetch product {product}"}
        
def get_product_by_ean(ean: str):
    """Lookup product by EAN barcode."""
    url = f"{BASE_URL}/products/ean/{ean}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "message": f"Failed to fetch product EAN {ean}"}

def search_physical_stores(search: str = None, group: str = None, lat: float = None, lng: float = None, km: int = None, size: int = 20, **kwargs):
    """
    Search for physical stores by location, name or group.
    
    Args:
        search: Keyword search (e.g., "Oslo").
        group: Chain name (e.g., "KIWI", "REMA_1000", "MENY_NO").
        lat, lng: Coordinates for proximity search.
        km: Search radius in km.
        size: Number of results (1-100).
    """
    # Handle aliases
    query = search or kwargs.get("location") or kwargs.get("query")
    
    url = f"{BASE_URL}/physical-stores"
    params = {}
    if query: params["search"] = query
    if group: params["group"] = group
    if lat: params["lat"] = lat
    if lng: params["lng"] = lng
    if km: params["km"] = km
    if size: params["size"] = size
    
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Optimization: Filter response to save tokens
        if "data" in data:
            optimized_data = []
            for s in data["data"]:
                optimized_data.append({
                    "name": s.get("name"),
                    "group": s.get("group"),
                    "address": s.get("address"),
                    "id": s.get("id")
                })
            return {"data": optimized_data}
        return data
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "message": "Failed to find stores"}

def find_physical_store_by_id(physicalStore: int):
    """Find physical store by ID."""
    url = f"{BASE_URL}/physical-stores/{physicalStore}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "message": f"Failed to fetch store {physicalStore}"}

def compare_product_prices_by_url(url: str):
    """Find product price comparison info by URL."""
    endpoint = f"{BASE_URL}/products/find-by-url/compare"
    params = {"url": url}
    try:
        response = requests.get(endpoint, headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "message": "Failed to compare prices"}

# Utility to format product output for the LLM
def format_product_list(products_data):
    """Helper to maintain a clean context for the LLM."""
    if "data" not in products_data:
        return "No products found."
        
    items = []
    for p in products_data["data"]:
        price = p.get("current_price") or "N/A"
        store_name = "Unknown Store"
        if p.get("store"):
           store_name = p["store"].get("name", "Unknown Store")
           
        items.append(f"- {p['name']} (Brand: {p.get('brand')}) - Price: {price} NOK at {store_name} (ID: {p['id']}, EAN: {p.get('ean')})")
    return "\n".join(items)
