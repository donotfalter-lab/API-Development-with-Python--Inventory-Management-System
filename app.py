from flask import Flask, jsonify, request

app = Flask(__name__)

INVENTORY = [
    {
        "id": 1,
        "barcode": "0819573020015",
        "product_name": "Organic Almond Milk",
        "brands": "Silk",
        "ingredients_text": "Filtered water, almonds, cane sugar, sea salt, vitamin A palmitate, vitamin D2, gellan gum.",
        "category": "Beverages",
        "quantity": 24,
        "price": 3.99,
    },
    {
        "id": 2,
        "barcode": "0038000138416",
        "product_name": "Honey Nut Cheerios",
        "brands": "General Mills",
        "ingredients_text": "Whole grain oats, sugar, corn starch, honey, brown sugar syrup, salt, tripotassium phosphate.",
        "category": "Breakfast Cereal",
        "quantity": 40,
        "price": 4.49,
    },
    {
        "id": 3,
        "barcode": "0044000032479",
        "product_name": "Ritz Original Crackers",
        "brands": "Nabisco",
        "ingredients_text": "Unbleached enriched flour, vegetable oil, sugar, salt, leavening, soy lecithin.",
        "category": "Snacks",
        "quantity": 15,
        "price": 3.29,
    },
    {
        "id": 4,
        "barcode": "0025293600024",
        "product_name": "Extra Virgin Olive Oil",
        "brands": "Bertolli",
        "ingredients_text": "Extra virgin olive oil.",
        "category": "Cooking Oils",
        "quantity": 8,
        "price": 9.99,
    },
]

REQUIRED_FIELDS = ["product_name", "quantity", "price"]


def find_item(item_id):
    return next((item for item in INVENTORY if item["id"] == item_id), None)


def next_id():
    return max((item["id"] for item in INVENTORY), default=0) + 1


@app.route("/inventory", methods=["GET"])
def get_inventory():
    return jsonify(INVENTORY), 200


@app.route("/inventory/<int:id>", methods=["GET"])
def get_item(id):
    item = find_item(id)
    if item is None:
        return jsonify({"error": f"No inventory item found with id {id}."}), 404
    return jsonify(item), 200


@app.route("/inventory", methods=["POST"])
def create_item():
    data = request.get_json(silent=True) or {}

    missing = [field for field in REQUIRED_FIELDS if field not in data]
    if missing:
        return jsonify({"error": f"Missing required field(s): {', '.join(missing)}"}), 400

    new_item = {
        "id": next_id(),
        "barcode": data.get("barcode", ""),
        "product_name": data["product_name"],
        "brands": data.get("brands", ""),
        "ingredients_text": data.get("ingredients_text", ""),
        "category": data.get("category", ""),
        "quantity": data["quantity"],
        "price": data["price"],
    }
    INVENTORY.append(new_item)
    return jsonify(new_item), 201


@app.route("/inventory/<int:id>", methods=["PATCH"])
def update_item(id):
    item = find_item(id)
    if item is None:
        return jsonify({"error": f"No inventory item found with id {id}."}), 404

    data = request.get_json(silent=True) or {}
    updatable_fields = [
        "barcode",
        "product_name",
        "brands",
        "ingredients_text",
        "category",
        "quantity",
        "price",
    ]
    for field in updatable_fields:
        if field in data:
            item[field] = data[field]

    return jsonify(item), 200


@app.route("/inventory/<int:id>", methods=["DELETE"])
def delete_item(id):
    item = find_item(id)
    if item is None:
        return jsonify({"error": f"No inventory item found with id {id}."}), 404

    INVENTORY.remove(item)
    return "", 204


if __name__ == "__main__":
    app.run(port=5555, debug=True)