import re
from datetime import datetime

from .market import QvixResult


def parse_push_times(value: str) -> set[str]:
    result = set()
    for item in re.split(r"[,，\s]+", value.strip()):
        if not item:
            continue
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", item):
            raise ValueError(f"无效推送时间: {item}，应为 HH:MM")
        result.add(item)
    return result


def build_group_sessions(value: str, platform_id: str) -> list[str]:
    sessions = []
    for item in re.split(r"[,，\s]+", value.strip()):
        if not item:
            continue
        session = f"{platform_id}:GroupMessage:{item}" if item.isdigit() else item
        if not re.fullmatch(r"[^:]+:GroupMessage:[^:]+", session):
            raise ValueError(f"无效 QQ 群会话: {item}")
        if session not in sessions:
            sessions.append(session)
    return sessions


def volatility_level(value: float) -> str:
    if value < 15:
        return "低波动"
    if value < 25:
        return "正常波动"
    if value < 35:
        return "波动偏高"
    return "高波动 / 恐慌"


def format_index_message(result: QvixResult) -> str:
    return "\n".join(
        [
            "A股恐慌指数（50ETF QVIX）",
            f"最新值：{result.value:.2f}",
            f"情绪参考：{volatility_level(result.value)}",
            f"分时时间：{result.quote_time}",
            f"获取时间：{result.fetched_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "数据来源：期权论坛 QVIX（第三方指标，非官方 iVIX）。",
        ]
    )


def is_weekday(moment: datetime) -> bool:
    return moment.weekday() < 5
