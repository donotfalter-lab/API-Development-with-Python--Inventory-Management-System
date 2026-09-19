import requests

BARCODE_LOOKUP_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"

REQUEST_TIMEOUT = 5


def fetch_product_by_barcode(barcode):
    """Look up a single product by its barcode. Returns a dict or None if not found."""
    url = BARCODE_LOOKUP_URL.format(barcode=barcode)
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()

    if data.get("status") != 1:
        return None

    return _extract_product_fields(data["product"])


def fetch_product_by_name(name):
    """Search for a product by name and return the first match, or None."""
    params = {
        "search_terms": name,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 1,
    }
    response = requests.get(SEARCH_URL, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()

    products = data.get("products", [])
    if not products:
        return None

    return _extract_product_fields(products[0])


def fetch_product_details(barcode=None, name=None):
    """Look up product details by barcode first, falling back to name search."""
    if barcode:
        return fetch_product_by_barcode(barcode)
    if name:
        return fetch_product_by_name(name)
    raise ValueError("Either a barcode or a name must be provided.")


def _extract_product_fields(product):
    """Pull out just the fields our inventory schema cares about."""
    categories = product.get("categories", "")
    first_category = categories.split(",")[0].strip() if categories else ""

    return {
        "barcode": product.get("code", ""),
        "product_name": product.get("product_name", ""),
        "brands": product.get("brands", ""),
        "ingredients_text": product.get("ingredients_text", ""),
        "category": first_category,
    }