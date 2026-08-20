import json
import unittest
from decimal import Decimal
from unittest.mock import Mock

from src.currency_rates import fetch_currency_rate


class CurrencyRatesTest(unittest.TestCase):
    def test_fetch_currency_rate_maps_nbp_response(self):
        response = Mock()
        response.text = json.dumps(
            {
                "table": "A",
                "currency": "euro",
                "code": "EUR",
                "rates": [
                    {
                        "no": "158/A/NBP/2026",
                        "effectiveDate": "2026-08-17",
                        "mid": 4.3075,
                    }
                ],
            }
        )
        client = Mock()
        client.get.return_value = response

        rate = fetch_currency_rate(client, "EUR")

        client.get.assert_called_once_with(
            "https://api.nbp.pl/api/exchangerates/rates/a/eur/",
            headers={"Accept": "application/json"},
        )
        response.raise_for_status.assert_called_once_with()
        self.assertEqual(rate.effective_date.isoformat(), "2026-08-17")
        self.assertEqual(rate.base_currency, "EUR")
        self.assertEqual(rate.quote_currency, "PLN")
        self.assertEqual(rate.rate_to_pln, Decimal("4.3075"))
        self.assertEqual(rate.provider, "NBP")
        self.assertEqual(rate.source_table, "158/A/NBP/2026")


if __name__ == "__main__":
    unittest.main()
