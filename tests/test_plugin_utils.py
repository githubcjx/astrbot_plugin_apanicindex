import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from core.market import QvixResult
from core.plugin_utils import (
    build_group_sessions,
    format_index_message,
    is_weekday,
    parse_push_times,
    volatility_level,
)


class PluginUtilsTests(unittest.TestCase):
    def test_parses_push_times(self):
        self.assertEqual(parse_push_times("09:35, 15:05，18:00"), {"09:35", "15:05", "18:00"})
        with self.assertRaises(ValueError):
            parse_push_times("25:00")

    def test_builds_deduplicated_group_sessions(self):
        sessions = build_group_sessions(
            "123456,789012\naiocqhttp:GroupMessage:123456", "aiocqhttp"
        )
        self.assertEqual(
            sessions,
            ["aiocqhttp:GroupMessage:123456", "aiocqhttp:GroupMessage:789012"],
        )
        with self.assertRaises(ValueError):
            build_group_sessions("webchat:FriendMessage:123", "aiocqhttp")

    def test_formats_result(self):
        now = datetime(2026, 10, 28, 15, 5, tzinfo=ZoneInfo("Asia/Shanghai"))
        message = format_index_message(QvixResult(20.123, "14:56:00", now))

        self.assertIn("最新值：20.12", message)
        self.assertIn("正常波动", message)
        self.assertIn("第三方指标", message)
        self.assertEqual(volatility_level(36), "高波动 / 恐慌")

    def test_weekday_filter(self):
        self.assertTrue(is_weekday(datetime(2026, 10, 28)))
        self.assertFalse(is_weekday(datetime(2026, 10, 31)))


if __name__ == "__main__":
    unittest.main()
