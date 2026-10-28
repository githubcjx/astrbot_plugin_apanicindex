import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from core.market import MarketDataError, parse_qvix_csv


class MarketTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 28, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    def test_reads_latest_valid_intraday_value(self):
        text = "Time,QVIX,Pre,max,min\n9:30:00,16.33,16.53,16.39,15.74\n9:32:17,16.35,,,\n15:00:00,,,,\n"

        result = parse_qvix_csv(text, self.now)

        self.assertEqual(result.value, 16.35)
        self.assertEqual(result.quote_time, "9:32:17")
        self.assertEqual(result.fetched_at, self.now)

    def test_rejects_empty_or_invalid_data(self):
        with self.assertRaises(MarketDataError):
            parse_qvix_csv("Time,QVIX\n15:00:00,NaN\n", self.now)


if __name__ == "__main__":
    unittest.main()
