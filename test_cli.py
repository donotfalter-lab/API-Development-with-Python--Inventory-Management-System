import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

import requests

import cli


class TestCLI(unittest.TestCase):
    def run_with_captured_output(self, func, *args, **kwargs):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            func(*args, **kwargs)
        return buffer.getvalue()

    # ---- safe_request ----
    @patch("cli.requests.request")
    def test_safe_request_returns_response_on_success(self, mock_request):
        mock_response = MagicMock(status_code=200)
        mock_request.return_value = mock_response

        result = cli.safe_request("GET", "http://localhost:5555/inventory")

        self.assertEqual(result, mock_response)

    @patch("cli.requests.request")
    def test_safe_request_handles_connection_error(self, mock_request):
        mock_request.side_effect = requests.exceptions.ConnectionError()

        output = self.run_with_captured_output(
            cli.safe_request, "GET", "http://localhost:5555/inventory"
        )

        self.assertIn("Could not connect", output)

    # ---- view_all_inventory ----
    @patch("cli.requests.request")
    def test_view_all_inventory_prints_items(self, mock_request):
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = [
            {"id": 1, "product_name": "Almond Milk", "quantity": 24, "price": 3.99, "barcode": "111"}
        ]
        mock_request.return_value = mock_response

        output = self.run_with_captured_output(cli.view_all_inventory)

        self.assertIn("Almond Milk", output)

    @patch("cli.requests.request")
    def test_view_all_inventory_handles_empty_list(self, mock_request):
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = []
        mock_request.return_value = mock_response

        output = self.run_with_captured_output(cli.view_all_inventory)

        self.assertIn("No inventory items found.", output)

    # ---- view_item_details ----
    @patch("cli.requests.request")
    @patch("builtins.input", return_value="1")
    def test_view_item_details_found(self, mock_input, mock_request):
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {"id": 1, "product_name": "Almond Milk"}
        mock_request.return_value = mock_response

        output = self.run_with_captured_output(cli.view_item_details)

        self.assertIn("Almond Milk", output)

    @patch("cli.requests.request")
    @patch("builtins.input", return_value="999")
    def test_view_item_details_not_found(self, mock_input, mock_request):
        mock_response = MagicMock(status_code=404)
        mock_request.return_value = mock_response

        output = self.run_with_captured_output(cli.view_item_details)

        self.assertIn("No item found", output)

    @patch("builtins.input", return_value="not-a-number")
    def test_view_item_details_invalid_id(self, mock_input):
        output = self.run_with_captured_output(cli.view_item_details)

        self.assertIn("valid whole number", output)

    # ---- add_new_item ----
    @patch("cli.requests.request")
    @patch("builtins.input")
    def test_add_new_item_success(self, mock_input, mock_request):
        mock_input.side_effect = ["", "Sparkling Water", "", "", "30", "1.25"]
        mock_response = MagicMock(status_code=201)
        mock_response.json.return_value = {"id": 5, "product_name": "Sparkling Water"}
        mock_request.return_value = mock_response

        output = self.run_with_captured_output(cli.add_new_item)

        self.assertIn("Added item #5", output)

    @patch("builtins.input")
    def test_add_new_item_invalid_quantity_cancels(self, mock_input):
        mock_input.side_effect = ["", "Sparkling Water", "", "", "not-a-number"]

        output = self.run_with_captured_output(cli.add_new_item)

        self.assertIn("valid whole number", output)

    @patch("cli.requests.request")
    @patch("builtins.input")
    def test_add_new_item_api_rejects_bad_input(self, mock_input, mock_request):
        mock_input.side_effect = ["", "", "", "", "5", "2.00"]
        mock_response = MagicMock(status_code=400)
        mock_response.json.return_value = {"error": "Missing required field(s): product_name"}
        mock_request.return_value = mock_response

        output = self.run_with_captured_output(cli.add_new_item)

        self.assertIn("Missing required field", output)

    # ---- update_item ----
    @patch("cli.requests.request")
    @patch("builtins.input")
    def test_update_item_price_only(self, mock_input, mock_request):
        mock_input.side_effect = ["1", "1", "5.99"]
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {"id": 1, "product_name": "Almond Milk", "price": 5.99}
        mock_request.return_value = mock_response

        output = self.run_with_captured_output(cli.update_item)

        self.assertIn("Updated item #1", output)
        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["json"], {"price": 5.99})

    @patch("builtins.input")
    def test_update_item_invalid_menu_choice(self, mock_input):
        mock_input.side_effect = ["1", "9"]

        output = self.run_with_captured_output(cli.update_item)

        self.assertIn("Invalid option", output)

    # ---- delete_item ----
    @patch("cli.requests.request")
    @patch("builtins.input")
    def test_delete_item_confirmed(self, mock_input, mock_request):
        mock_input.side_effect = ["1", "y"]
        mock_response = MagicMock(status_code=204)
        mock_request.return_value = mock_response

        output = self.run_with_captured_output(cli.delete_item)

        self.assertIn("Deleted item #1", output)

    @patch("builtins.input")
    def test_delete_item_cancelled(self, mock_input):
        mock_input.side_effect = ["1", "n"]

        output = self.run_with_captured_output(cli.delete_item)

        self.assertIn("Cancelled", output)

    # ---- find_item_on_api ----
    @patch("cli.requests.request")
    @patch("builtins.input")
    def test_find_item_on_api_by_barcode(self, mock_input, mock_request):
        mock_input.side_effect = ["1", "0819573020015"]
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {"product_name": "Almond Milk"}
        mock_request.return_value = mock_response

        output = self.run_with_captured_output(cli.find_item_on_api)

        self.assertIn("Product Found", output)
        self.assertIn("Almond Milk", output)

    @patch("cli.requests.request")
    @patch("builtins.input")
    def test_find_item_on_api_not_found(self, mock_input, mock_request):
        mock_input.side_effect = ["2", "nonexistent product"]
        mock_response = MagicMock(status_code=404)
        mock_request.return_value = mock_response

        output = self.run_with_captured_output(cli.find_item_on_api)

        self.assertIn("No matching product", output)

    @patch("builtins.input")
    def test_find_item_on_api_empty_barcode(self, mock_input):
        mock_input.side_effect = ["1", ""]

        output = self.run_with_captured_output(cli.find_item_on_api)

        self.assertIn("cannot be empty", output)


if __name__ == "__main__":
    unittest.main()