import unittest
from unittest.mock import patch

import requests

from app import app, INVENTORY


class TestInventoryAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        INVENTORY.clear()
        INVENTORY.extend(
            [
                {
                    "id": 1,
                    "barcode": "0819573020015",
                    "product_name": "Organic Almond Milk",
                    "brands": "Silk",
                    "ingredients_text": "Filtered water, almonds, cane sugar.",
                    "category": "Beverages",
                    "quantity": 24,
                    "price": 3.99,
                },
                {
                    "id": 2,
                    "barcode": "0038000138416",
                    "product_name": "Honey Nut Cheerios",
                    "brands": "General Mills",
                    "ingredients_text": "Whole grain oats, sugar.",
                    "category": "Breakfast Cereal",
                    "quantity": 40,
                    "price": 4.49,
                },
            ]
        )

    # ---- GET /inventory ----
    def test_get_all_inventory(self):
        response = self.client.get("/inventory")
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["product_name"], "Organic Almond Milk")

    # ---- GET /inventory/<id> ----
    def test_get_single_item_found(self):
        response = self.client.get("/inventory/1")
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["product_name"], "Organic Almond Milk")

    def test_get_single_item_not_found(self):
        response = self.client.get("/inventory/999")

        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.get_json())

    # ---- POST /inventory ----
    @patch("app.fetch_product_details")
    def test_create_item_without_barcode(self, mock_fetch):
        payload = {"product_name": "Sparkling Water", "quantity": 30, "price": 1.25}
        response = self.client.post("/inventory", json=payload)
        data = response.get_json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(data["product_name"], "Sparkling Water")
        self.assertEqual(data["id"], 3)
        mock_fetch.assert_not_called()

    @patch("app.fetch_product_details")
    def test_create_item_with_barcode_enriches_from_api(self, mock_fetch):
        mock_fetch.return_value = {
            "barcode": "1234567890",
            "product_name": "Mock Product",
            "brands": "Mock Brand",
            "ingredients_text": "Mock ingredients.",
            "category": "Mock Category",
        }
        payload = {"barcode": "1234567890", "quantity": 10, "price": 2.50}
        response = self.client.post("/inventory", json=payload)
        data = response.get_json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(data["product_name"], "Mock Product")
        self.assertEqual(data["brands"], "Mock Brand")
        mock_fetch.assert_called_once_with(barcode="1234567890")

    def test_create_item_missing_required_fields(self):
        response = self.client.post("/inventory", json={"product_name": "Incomplete Item"})
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", data)

    # ---- PATCH /inventory/<id> ----
    def test_update_item_success(self):
        response = self.client.patch("/inventory/1", json={"price": 4.99, "quantity": 50})
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["price"], 4.99)
        self.assertEqual(data["quantity"], 50)

    def test_update_item_not_found(self):
        response = self.client.patch("/inventory/999", json={"price": 1.00})

        self.assertEqual(response.status_code, 404)

    def test_update_item_ignores_unknown_fields(self):
        response = self.client.patch("/inventory/1", json={"made_up_field": "nope"})
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("made_up_field", data)

    # ---- DELETE /inventory/<id> ----
    def test_delete_item_success(self):
        response = self.client.delete("/inventory/1")
        self.assertEqual(response.status_code, 204)

        follow_up = self.client.get("/inventory/1")
        self.assertEqual(follow_up.status_code, 404)

    def test_delete_item_not_found(self):
        response = self.client.delete("/inventory/999")

        self.assertEqual(response.status_code, 404)

    # ---- GET /products/lookup ----
    @patch("app.fetch_product_details")
    def test_lookup_product_found(self, mock_fetch):
        mock_fetch.return_value = {
            "barcode": "1111111111",
            "product_name": "Found Product",
            "brands": "Some Brand",
            "ingredients_text": "",
            "category": "",
        }
        response = self.client.get("/products/lookup?barcode=1111111111")
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["product_name"], "Found Product")
        mock_fetch.assert_called_once_with(barcode="1111111111", name=None)

    @patch("app.fetch_product_details")
    def test_lookup_product_not_found(self, mock_fetch):
        mock_fetch.return_value = None
        response = self.client.get("/products/lookup?barcode=0000000000")

        self.assertEqual(response.status_code, 404)

    def test_lookup_product_missing_params(self):
        response = self.client.get("/products/lookup")

        self.assertEqual(response.status_code, 400)

    @patch("app.fetch_product_details")
    def test_lookup_product_api_failure(self, mock_fetch):
        mock_fetch.side_effect = requests.exceptions.ConnectionError()
        response = self.client.get("/products/lookup?name=anything")

        self.assertEqual(response.status_code, 503)

    # ---- PATCH /inventory/<id>/refresh ----
    @patch("app.fetch_product_details")
    def test_refresh_item_success(self, mock_fetch):
        mock_fetch.return_value = {
            "product_name": "Updated Name",
            "brands": "Updated Brand",
            "ingredients_text": "Updated ingredients.",
            "category": "Updated Category",
        }
        response = self.client.patch("/inventory/1/refresh")
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["product_name"], "Updated Name")
        mock_fetch.assert_called_once_with(barcode="0819573020015")

    def test_refresh_item_no_barcode(self):
        INVENTORY[0]["barcode"] = ""
        response = self.client.patch("/inventory/1/refresh")

        self.assertEqual(response.status_code, 400)

    def test_refresh_item_not_found(self):
        response = self.client.patch("/inventory/999/refresh")

        self.assertEqual(response.status_code, 404)

    # ---- GET /health ----
    def test_health_check(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()