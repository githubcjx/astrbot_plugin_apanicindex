import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, MessageChain, filter
from astrbot.api.star import Context, Star, register

from .core.market import fetch_50etf_qvix
from .core.plugin_utils import (
    build_group_sessions,
    format_index_message,
    is_weekday,
    parse_push_times,
)


SHANGHAI = ZoneInfo("Asia/Shanghai")


@register(
    "astrbot_plugin_apanicindex",
    "githubcjx",
    "获取 50ETF QVIX 恐慌指数，并定时推送到 QQ 群",
    "1.0.0",
)
class APanicIndexPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig | None = None):
        super().__init__(context)
        self.config = config or {}
        self._scheduler_task: asyncio.Task | None = None
        self._fetch_lock = asyncio.Lock()
        self._last_push_date = None
        self._last_push_slots: set[str] = set()

    async def initialize(self):
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())

    async def terminate(self):
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass

    def _setting(self, name, default):
        return self.config.get(name, default)

    async def _load_message(self) -> str:
        async with self._fetch_lock:
            result = await asyncio.to_thread(fetch_50etf_qvix)
        return format_index_message(result)

    async def _push_to_groups(self):
        sessions = build_group_sessions(
            str(self._setting("push_groups", "")),
            str(self._setting("platform_id", "aiocqhttp")),
        )
        if not sessions:
            logger.warning("A股恐慌指数：已到达推送时间，但未配置目标 QQ 群")
            return

        message = await self._load_message()
        for session in sessions:
            try:
                await self.context.send_message(session, MessageChain().message(message))
            except Exception:
                logger.exception(f"A股恐慌指数：推送到 {session} 失败")

    async def _check_schedule(self):
        if not self._setting("push_enabled", True):
            return
        now = datetime.now(SHANGHAI)
        if self._setting("trading_day_only", True) and not is_weekday(now):
            return

        current_date = now.date()
        if current_date != self._last_push_date:
            self._last_push_date = current_date
            self._last_push_slots.clear()

        slot = now.strftime("%H:%M")
        if (
            slot in parse_push_times(str(self._setting("push_times", "09:35,15:05")))
            and slot not in self._last_push_slots
        ):
            self._last_push_slots.add(slot)
            await self._push_to_groups()

    async def _scheduler_loop(self):
        while True:
            try:
                await self._check_schedule()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("A股恐慌指数：定时推送任务执行失败")
            await asyncio.sleep(15)

    @filter.command("apanicindex")
    async def query_index(self, event: AstrMessageEvent):
        try:
            message = await self._load_message()
        except Exception as exc:
            logger.exception("A股恐慌指数：手动查询失败")
            yield event.plain_result(f"暂时无法获取 A 股恐慌指数：{exc}")
            return
        yield event.plain_result(message)
