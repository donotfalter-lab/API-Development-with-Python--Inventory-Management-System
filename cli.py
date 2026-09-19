import sys

import requests

BASE_URL = "http://localhost:5555"


def safe_request(method, url, **kwargs):
    """Wraps requests calls so connection issues don't crash the CLI."""
    timeout = kwargs.pop("timeout", 5)
    try:
        return requests.request(method, url, timeout=timeout, **kwargs)
    except requests.exceptions.ConnectionError:
        print("Could not connect to the API. Is the Flask server running on port 5555?")
    except requests.exceptions.Timeout:
        print("The request timed out. The server may be slow or unreachable.")
    except requests.exceptions.RequestException as error:
        print(f"An unexpected network error occurred: {error}")
    return None


def prompt_for_int(message):
    value = input(message).strip()
    try:
        return int(value)
    except ValueError:
        print("Please enter a valid whole number.")
        return None


def prompt_for_float(message):
    value = input(message).strip()
    try:
        return float(value)
    except ValueError:
        print("Please enter a valid number.")
        return None


def view_all_inventory():
    response = safe_request("GET", f"{BASE_URL}/inventory")
    if response is None:
        return

    if response.status_code != 200:
        print(f"Unexpected error ({response.status_code}).")
        return

    items = response.json()
    if not items:
        print("No inventory items found.")
        return

    print(f"\n{'ID':<4} {'Name':<30} {'Qty':<6} {'Price':<8} {'Barcode'}")
    print("-" * 70)
    for item in items:
        print(
            f"{item['id']:<4} {item['product_name']:<30} {item['quantity']:<6} "
            f"${item['price']:<7.2f} {item.get('barcode', '')}"
        )


def view_item_details():
    item_id = prompt_for_int("Enter item ID: ")
    if item_id is None:
        return

    response = safe_request("GET", f"{BASE_URL}/inventory/{item_id}")
    if response is None:
        return

    if response.status_code == 404:
        print(f"No item found with ID {item_id}.")
        return
    if response.status_code != 200:
        print(f"Unexpected error ({response.status_code}).")
        return

    item = response.json()
    print("\n--- Item Details ---")
    for key, value in item.items():
        print(f"{key}: {value}")


def add_new_item():
    print("\n--- Add New Item ---")
    barcode = input("Barcode (leave blank to skip API lookup): ").strip()

    payload = {}
    if barcode:
        payload["barcode"] = barcode

    product_name = input("Product name (leave blank to use API data if available): ").strip()
    if product_name:
        payload["product_name"] = product_name

    brands = input("Brand (optional): ").strip()
    if brands:
        payload["brands"] = brands

    category = input("Category (optional): ").strip()
    if category:
        payload["category"] = category

    quantity = prompt_for_int("Quantity in stock: ")
    if quantity is None:
        return
    payload["quantity"] = quantity

    price = prompt_for_float("Price: ")
    if price is None:
        return
    payload["price"] = price

    response = safe_request("POST", f"{BASE_URL}/inventory", json=payload)
    if response is None:
        return

    if response.status_code == 201:
        item = response.json()
        print(f"\nAdded item #{item['id']}: {item['product_name']}")
    elif response.status_code == 400:
        error = response.json().get("error", "Invalid input.")
        print(f"Could not add item: {error}")
    else:
        print(f"Unexpected error ({response.status_code}).")


def update_item():
    item_id = prompt_for_int("Enter item ID to update: ")
    if item_id is None:
        return

    print("What would you like to update?")
    print("1. Price")
    print("2. Quantity (stock level)")
    print("3. Both")
    choice = input("Choose an option: ").strip()

    if choice not in ("1", "2", "3"):
        print("Invalid option.")
        return

    payload = {}
    if choice in ("1", "3"):
        price = prompt_for_float("New price: ")
        if price is None:
            return
        payload["price"] = price

    if choice in ("2", "3"):
        quantity = prompt_for_int("New quantity: ")
        if quantity is None:
            return
        payload["quantity"] = quantity

    response = safe_request("PATCH", f"{BASE_URL}/inventory/{item_id}", json=payload)
    if response is None:
        return

    if response.status_code == 200:
        item = response.json()
        print(f"\nUpdated item #{item['id']}: {item['product_name']}")
    elif response.status_code == 404:
        print(f"No item found with ID {item_id}.")
    else:
        print(f"Unexpected error ({response.status_code}).")


def delete_item():
    item_id = prompt_for_int("Enter item ID to delete: ")
    if item_id is None:
        return

    confirm = input(f"Are you sure you want to delete item #{item_id}? (y/n): ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    response = safe_request("DELETE", f"{BASE_URL}/inventory/{item_id}")
    if response is None:
        return

    if response.status_code == 204:
        print(f"Deleted item #{item_id}.")
    elif response.status_code == 404:
        print(f"No item found with ID {item_id}.")
    else:
        print(f"Unexpected error ({response.status_code}).")


def find_item_on_api():
    print("\n--- Find Product on OpenFoodFacts ---")
    print("1. Search by barcode")
    print("2. Search by name")
    choice = input("Choose an option: ").strip()

    params = {}
    if choice == "1":
        barcode = input("Enter barcode: ").strip()
        if not barcode:
            print("Barcode cannot be empty.")
            return
        params["barcode"] = barcode
    elif choice == "2":
        name = input("Enter product name: ").strip()
        if not name:
            print("Name cannot be empty.")
            return
        params["name"] = name
    else:
        print("Invalid option.")
        return

    response = safe_request("GET", f"{BASE_URL}/products/lookup", params=params, timeout=10)
    if response is None:
        return

    if response.status_code == 200:
        product = response.json()
        print("\n--- Product Found ---")
        for key, value in product.items():
            print(f"{key}: {value}")
    elif response.status_code == 404:
        print("No matching product was found.")
    elif response.status_code == 503:
        print("The OpenFoodFacts API is currently unavailable. Try again later.")
    else:
        print(f"Unexpected error ({response.status_code}).")


MENU = """
==== Inventory Management CLI ====
1. View all inventory
2. View item details
3. Add new item
4. Update item price/stock
5. Delete item
6. Find item on OpenFoodFacts
7. Exit
"""


def main():
    while True:
        print(MENU)
        choice = input("Choose an option: ").strip()

        if choice == "1":
            view_all_inventory()
        elif choice == "2":
            view_item_details()
        elif choice == "3":
            add_new_item()
        elif choice == "4":
            update_item()
        elif choice == "5":
            delete_item()
        elif choice == "6":
            find_item_on_api()
        elif choice == "7":
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Invalid option. Please choose a number from 1 to 7.")


if __name__ == "__main__":
    main()