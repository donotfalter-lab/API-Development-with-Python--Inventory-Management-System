# Inventory Management System

A Flask REST API and command line client for managing retail inventory, with
product lookups powered by the [OpenFoodFacts](https://world.openfoodfacts.org/)
API. Built as an administrator portal for adding, editing, viewing, and
deleting inventory items, with the option to auto-fill product details
(brand, ingredients, category) by barcode or name instead of typing them in
by hand.

## Project structure

```
.
├── app.py              # Flask REST API and in-memory inventory "database"
├── external_api.py     # OpenFoodFacts integration (barcode/name lookups)
├── cli.py               # Command line client that talks to the API over HTTP
├── test_app.py          # Unit tests for the API endpoints
├── test_external_api.py # Unit tests for the OpenFoodFacts integration
├── test_cli.py           # Unit tests for the CLI
└── README.md
```

## Installation and setup

### 1. Clone the repository

```bash
git clone git@github.com:donotfalter-lab/API-Development-with-Python--Inventory-Management-System.git
cd API-Development-with-Python--Inventory-Management-System
```

### 2. Install dependencies

Using `pipenv` (recommended, matches the `Pipfile` in this repo):

```bash
pipenv install
pipenv shell
```

Or with `pip` in a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
pip install flask requests
```

### 3. Run the API server

```bash
python app.py
```

The server starts on `http://localhost:5555` with debug mode on. Leave this
running in its own terminal window.

### 4. Run the CLI (in a separate terminal)

```bash
python cli.py
```

The CLI expects the API server to already be running on `localhost:5555`. If
it isn't, CLI commands will print a connection error instead of crashing.

### 5. Run the tests

```bash
pytest
```

or, without pytest installed:

```bash
python -m unittest discover
```

All three test files mock outbound HTTP calls, so the test suite runs
without needing the API server up or real network access to OpenFoodFacts.

## API endpoint details

The API stores inventory in an in-memory Python list (`INVENTORY` in
`app.py`), which resets whenever the server restarts. Each item has this
shape:

```json
{
  "id": 1,
  "barcode": "0819573020015",
  "product_name": "Organic Almond Milk",
  "brands": "Silk",
  "ingredients_text": "Filtered water, almonds, cane sugar, ...",
  "category": "Beverages",
  "quantity": 24,
  "price": 3.99
}
```

| Method | Route | Description | Body / Params | Success | Failure |
|---|---|---|---|---|---|
| `GET` | `/inventory` | List all inventory items | none | `200`, JSON array | — |
| `GET` | `/inventory/<id>` | Get one item by ID | none | `200`, JSON object | `404` if no item with that ID |
| `POST` | `/inventory` | Add a new item | JSON body: `product_name`, `quantity`, `price` required; `barcode`, `brands`, `category`, `ingredients_text` optional | `201`, JSON of created item | `400` if required fields are missing |
| `PATCH` | `/inventory/<id>` | Update one or more fields on an item | JSON body with any subset of updatable fields | `200`, JSON of updated item | `404` if no item with that ID |
| `DELETE` | `/inventory/<id>` | Remove an item | none | `204`, empty body | `404` if no item with that ID |
| `PATCH` | `/inventory/<id>/refresh` | Re-fetch this item's product details from OpenFoodFacts using its stored barcode | none | `200`, JSON of updated item | `400` if item has no barcode on file; `404` if item or product not found; `503` if OpenFoodFacts is unreachable |
| `GET` | `/products/lookup` | Look up a product on OpenFoodFacts without adding it to inventory | Query param `barcode` or `name` | `200`, JSON of product data | `400` if neither param given; `404` if no match; `503` if OpenFoodFacts is unreachable |
| `GET` | `/health` | Health check | none | `200`, `{"status": "ok"}` | — |

A note on `POST /inventory`: if you supply a `barcode` but leave out fields
like `product_name`, `brands`, or `category`, the API will try to fill those
in automatically from OpenFoodFacts before validating the request. `quantity`
and `price` are always required directly from you, since OpenFoodFacts
doesn't track a retailer's stock levels or pricing.

## Example CLI usage

Run `python cli.py` to launch the interactive menu:

```
==== Inventory Management CLI ====
1. View all inventory
2. View item details
3. Add new item
4. Update item price/stock
5. Delete item
6. Find item on OpenFoodFacts
7. Exit

Choose an option:
```

**Viewing all inventory (option 1)**

```
Choose an option: 1

ID   Name                           Qty    Price    Barcode
----------------------------------------------------------------------
1    Organic Almond Milk           24     $3.99    0819573020015
2    Honey Nut Cheerios            40     $4.49    0038000138416
```

**Adding a new item by barcode (option 3)**

```
Choose an option: 3

--- Add New Item ---
Barcode (leave blank to skip API lookup): 0819573020015
Product name (leave blank to use API data if available):
Brand (optional):
Category (optional):
Quantity in stock: 24
Price: 3.99

Added item #5: Organic Almond Milk
```

Leaving `product_name`, `brands`, and `category` blank here lets the API
pull those fields from OpenFoodFacts using the barcode you provided.

**Updating stock or price (option 4)**

```
Choose an option: 4
Enter item ID to update: 2
What would you like to update?
1. Price
2. Quantity (stock level)
3. Both
Choose an option: 2
New quantity: 35

Updated item #2: Honey Nut Cheerios
```

**Looking up a product before adding it (option 6)**

```
Choose an option: 6

--- Find Product on OpenFoodFacts ---
1. Search by barcode
2. Search by name
Choose an option: 2
Enter product name: almond milk

--- Product Found ---
barcode: 0819573020015
product_name: Organic Almond Milk
brands: Silk
ingredients_text: Filtered water, almonds, cane sugar, ...
category: Beverages
```

This lookup doesn't add anything to inventory by itself, it's a preview. To
actually add what you found, take the barcode back to option 3.

**Deleting an item (option 5)**

```
Choose an option: 5
Enter item ID to delete: 4
Are you sure you want to delete item #4? (y/n): y

Deleted item #4.
```

## Error handling

Both the API and the CLI are written to fail gracefully rather than crash:

- The API validates required fields on `POST` and returns `400` with a
  clear message rather than a stack trace.
- Any route touching OpenFoodFacts catches network failures and returns
  `503` instead of letting an unhandled exception take the server down.
- The CLI wraps every HTTP call in a `safe_request()` helper that catches
  connection errors and timeouts, printing a friendly message and returning
  to the menu instead of crashing the program.
- Numeric CLI prompts (`quantity`, `price`, item IDs) are validated before
  being sent to the API, so a typo just re-prompts or cancels that action
  rather than sending garbage to the server.

## Code style and maintainability

- `app.py`, `external_api.py`, and `cli.py` are kept as separate modules
  with a single responsibility each: `app.py` only handles HTTP
  routing and request/response shaping, `external_api.py` only knows how to
  talk to OpenFoodFacts, and `cli.py` only knows how to talk to this
  project's own API. None of them reach into each other's internals.
- Small helper functions (`find_item`, `next_id` in `app.py`;
  `safe_request`, `prompt_for_int`, `prompt_for_float` in `cli.py`) exist to
  avoid repeating the same lookup, ID-generation, or input-validation logic
  across multiple routes or menu options.
- Functions in `external_api.py` and the route handlers in `app.py` include
  docstrings explaining what they do and what they return, particularly
  around the less obvious behavior (like `PATCH` only overwriting fields
  present in the request body, or `POST` merging API data with user input
  so user-supplied values always win).
- Each of the three modules has its own test file, so a change to one part
  of the system (say, the OpenFoodFacts response format) surfaces failures
  in the specific test file responsible for that layer, rather than one
  giant test file that's unclear about what broke.