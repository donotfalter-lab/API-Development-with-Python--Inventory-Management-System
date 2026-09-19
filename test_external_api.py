import unittest
from unittest.mock import MagicMock, patch

import requests

from external_api import (
    fetch_product_by_barcode,
    fetch_product_by_name,
    fetch_product_details,
)


class TestExternalAPI(unittest.TestCase):
    @patch("external_api.requests.get")
    def test_fetch_product_by_barcode_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": 1,
            "product": {
                "code": "0819573020015",
                "product_name": "Organic Almond Milk",
                "brands": "Silk",
                "ingredients_text": "Filtered water, almonds.",
                "categories": "Beverages, Plant-based milk",
            },
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = fetch_product_by_barcode("0819573020015")

        self.assertEqual(result["product_name"], "Organic Almond Milk")
        self.assertEqual(result["category"], "Beverages")
        mock_get.assert_called_once()

    @patch("external_api.requests.get")
    def test_fetch_product_by_barcode_not_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": 0}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = fetch_product_by_barcode("0000000000000")

        self.assertIsNone(result)

    @patch("external_api.requests.get")
    def test_fetch_product_by_barcode_raises_on_http_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 error")
        mock_get.return_value = mock_response

        with self.assertRaises(requests.exceptions.HTTPError):
            fetch_product_by_barcode("0000000000000")

    @patch("external_api.requests.get")
    def test_fetch_product_by_name_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "products": [
                {
                    "code": "1234567890",
                    "product_name": "Mock Cereal",
                    "brands": "Mock Brand",
                    "ingredients_text": "Oats, sugar.",
                    "categories": "Cereals",
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = fetch_product_by_name("cereal")

        self.assertEqual(result["product_name"], "Mock Cereal")
        mock_get.assert_called_once()

    @patch("external_api.requests.get")
    def test_fetch_product_by_name_no_results(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"products": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = fetch_product_by_name("nonexistent product xyz")

        self.assertIsNone(result)

    def test_fetch_product_details_requires_barcode_or_name(self):
        with self.assertRaises(ValueError):
            fetch_product_details()

    @patch("external_api.fetch_product_by_barcode")
    def test_fetch_product_details_prefers_barcode(self, mock_by_barcode):
        mock_by_barcode.return_value = {"product_name": "From Barcode"}

        result = fetch_product_details(barcode="123", name="ignored")

        self.assertEqual(result["product_name"], "From Barcode")
        mock_by_barcode.assert_called_once_with("123")


if __name__ == "__main__":
    unittest.main()