import sys
import types
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo


astrbot = types.ModuleType("astrbot")
api = types.ModuleType("astrbot.api")
event = types.ModuleType("astrbot.api.event")
star = types.ModuleType("astrbot.api.star")


class Logger:
    def warning(self, *args):
        pass

    def exception(self, *args):
        pass


class MessageChain:
    def __init__(self):
        self.text = ""

    def message(self, text):
        self.text = text
        return self


class Filter:
    def command(self, name):
        return lambda function: function


class Star:
    def __init__(self, context):
        self.context = context


class AstrBotConfig(dict):
    pass


api.AstrBotConfig = AstrBotConfig
api.logger = Logger()
event.AstrMessageEvent = type("AstrMessageEvent", (), {})
event.MessageChain = MessageChain
event.filter = Filter()
star.Context = type("Context", (), {})
star.Star = Star
star.register = lambda *args: lambda cls: cls
sys.modules.update(
    {
        "astrbot": astrbot,
        "astrbot.api": api,
        "astrbot.api.event": event,
        "astrbot.api.star": star,
    }
)

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from astrbot_plugin_apanicindex.core.market import QvixResult
from astrbot_plugin_apanicindex.main import APanicIndexPlugin


class Context:
    def __init__(self):
        self.sent = []

    async def send_message(self, session, message_chain):
        self.sent.append((session, message_chain.text))


class MainTests(unittest.IsolatedAsyncioTestCase):
    def result(self):
        now = datetime(2026, 10, 28, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
        return QvixResult(16.07, "09:59:00", now)

    async def test_pushes_one_value_to_all_groups(self):
        context = Context()
        plugin = APanicIndexPlugin(
            context,
            {
                "push_groups": "123456,789012",
                "platform_id": "aiocqhttp",
            },
        )

        with patch(
            "astrbot_plugin_apanicindex.main.fetch_50etf_qvix",
            return_value=self.result(),
        ):
            await plugin._push_to_groups()

        self.assertEqual(len(context.sent), 2)
        self.assertEqual(context.sent[0][0], "aiocqhttp:GroupMessage:123456")
        self.assertIn("16.07", context.sent[0][1])
        self.assertEqual(context.sent[1][0], "aiocqhttp:GroupMessage:789012")

    async def test_schedule_only_runs_once_per_minute(self):
        now = datetime(2026, 10, 28, 9, 35, 20, tzinfo=ZoneInfo("Asia/Shanghai"))
        plugin = APanicIndexPlugin(
            Context(),
            {
                "push_enabled": True,
                "trading_day_only": True,
                "push_times": "09:35",
                "push_groups": "123456",
            },
        )
        plugin._push_to_groups = AsyncMock()

        with patch("astrbot_plugin_apanicindex.main.datetime") as datetime_mock:
            datetime_mock.now.return_value = now
            await plugin._check_schedule()
            await plugin._check_schedule()

        plugin._push_to_groups.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
