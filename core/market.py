import csv
import io
import math
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from requests.adapters import HTTPAdapter


SHANGHAI = ZoneInfo("Asia/Shanghai")
QVIX_URL = "http://1.optbbs.com/d/csv/d/vix50.csv"


class MarketDataError(RuntimeError):
    pass


@dataclass(frozen=True)
class QvixResult:
    value: float
    quote_time: str
    fetched_at: datetime


def parse_qvix_csv(text: str, fetched_at: datetime) -> QvixResult:
    latest_value = None
    latest_time = None
    for row in csv.reader(io.StringIO(text)):
        if len(row) < 2:
            continue
        quote_time = row[0].strip()
        try:
            datetime.strptime(quote_time, "%H:%M:%S")
            value = float(row[1].strip())
        except ValueError:
            continue
        if math.isfinite(value) and value > 0:
            latest_time = quote_time
            latest_value = value
    if latest_value is None or latest_time is None:
        raise MarketDataError("QVIX 分时数据中没有有效数值")
    return QvixResult(latest_value, latest_time, fetched_at)


def fetch_50etf_qvix(as_of: datetime | None = None) -> QvixResult:
    fetched_at = as_of or datetime.now(SHANGHAI)
    try:
        with requests.Session() as session:
            session.trust_env = False
            session.mount("http://", HTTPAdapter(max_retries=2))
            response = session.get(QVIX_URL, timeout=15)
            response.raise_for_status()
    except requests.RequestException as exc:
        raise MarketDataError(f"获取 50ETF QVIX 失败: {exc}") from exc
    return parse_qvix_csv(response.content.decode("utf-8-sig"), fetched_at)
