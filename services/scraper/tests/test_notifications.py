import os
import unittest
from unittest.mock import Mock, patch

from src.notifications import notify_scraper_failed, notify_scraper_succeeded


class DiscordNotificationTests(unittest.TestCase):
    @patch.dict(os.environ, {"DISCORD_WEBHOOK_URL": "https://example.test/webhook"})
    @patch("src.notifications.httpx.post")
    def test_success_message_contains_run_details(self, post):
        post.return_value = Mock()

        notify_scraper_succeeded(
            "run-123",
            42,
            1.25,
            [
                {
                    "title": "Porsche 911",
                    "brand": "Porsche",
                    "model": "911",
                    "year": 2024,
                    "mileage_km": 50000,
                    "price_amount": 5000000,
                    "price_currency": "EUR",
                    "url": "https://example.test/offer",
                }
            ],
        )

        content = post.call_args.kwargs["json"]["content"]
        self.assertIn("Beamer scraper completed", content)
        self.assertIn("run-123", content)
        self.assertIn("42", content)
        self.assertIn("Porsche 911", content)
        self.assertIn("https://example.test/offer", content)
        post.return_value.raise_for_status.assert_called_once_with()

    @patch.dict(os.environ, {"DISCORD_WEBHOOK_URL": "https://example.test/webhook"})
    @patch("src.notifications.httpx.post")
    def test_failure_message_contains_error(self, post):
        post.return_value = Mock()

        notify_scraper_failed(ValueError("bad response"), 2.0)

        content = post.call_args.kwargs["json"]["content"]
        self.assertIn("Beamer scraper failed", content)
        self.assertIn("ValueError: bad response", content)


if __name__ == "__main__":
    unittest.main()
