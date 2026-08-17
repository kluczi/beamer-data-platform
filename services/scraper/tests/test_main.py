import unittest
from unittest.mock import Mock, patch

from src import main as scraper_main


class ScraperMainTests(unittest.TestCase):
    def test_success_sends_discord_alert(self):
        connection = Mock()

        with (
            patch.object(scraper_main, "initialize_warehouse"),
            patch.object(scraper_main, "load_into_datalake", return_value="run-123"),
            patch.object(scraper_main, "get_connection", return_value=connection),
            patch.object(scraper_main, "load_pending_scrape_runs", return_value=42),
            patch.object(scraper_main, "notify_scraper_succeeded") as notify_succeeded,
            patch.object(scraper_main, "notify_scraper_failed") as notify_failed,
        ):
            scraper_main.main()

        connection.close.assert_called_once_with()
        notify_succeeded.assert_called_once()
        self.assertEqual(notify_succeeded.call_args.args[:2], ("run-123", 42))
        self.assertEqual(notify_succeeded.call_args.args[3], [])
        notify_failed.assert_not_called()

    def test_failure_sends_discord_alert_and_reraises(self):
        scraper_error = ValueError("scrape failed")

        with (
            patch.object(
                scraper_main,
                "initialize_warehouse",
                side_effect=scraper_error,
            ),
            patch.object(scraper_main, "notify_scraper_failed") as notify_failed,
        ):
            with self.assertRaisesRegex(ValueError, "scrape failed"):
                scraper_main.main()

        notify_failed.assert_called_once()
        self.assertIs(notify_failed.call_args.args[0], scraper_error)

    def test_discord_failure_does_not_replace_scraper_error(self):
        with (
            patch.object(
                scraper_main,
                "initialize_warehouse",
                side_effect=ValueError("scrape failed"),
            ),
            patch.object(
                scraper_main,
                "notify_scraper_failed",
                side_effect=RuntimeError("Discord unavailable"),
            ),
        ):
            with self.assertRaisesRegex(ValueError, "scrape failed"):
                scraper_main.main()


if __name__ == "__main__":
    unittest.main()
