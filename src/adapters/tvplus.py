"""
TV+ (tvplus.com.tr) — BİRİNCİL kaynak. En zengin: başlık + başlangıç + bitiş + tür + tam açıklama, ~10 gün.

Yayın akışı URL'si:  https://tvplus.com.tr/canli-tv/yayin-akisi/{slug}
   slug örn: star-tv-hd--89, trt1-hd--144, s-sport--11

TV+ Next.js. Program verisi genelde <script id="__NEXT_DATA__"> JSON'unda gömülü.
Aşağıdaki parser JSON'u recursively tarayıp "program gibi" nesneleri bulur
(başlangıç/bitiş zamanı + ad alanları olan dict'ler).

>>> CANLI HTML'E GÖRE AYAR GEREKEBİLİR <<<
PC'de bir kez `print(json.dumps(data, ...))` ile __NEXT_DATA__ şemasına bak,
aşağıdaki alan adlarını (START_KEYS/TITLE_KEYS/DESC_KEYS) doğrula.
"""
from __future__ import annotations
import json
import re
from datetime import datetime, timezone, timedelta
from typing import List, Any

from bs4 import BeautifulSoup
from dateutil import parser as dtparse

from adapters.base import BaseAdapter
from models import Programme
from normalize import IST, ist, parse_hhmm_on

TIME_RANGE_RE = re.compile(r"(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})")
KNOWN_CATS = {"Dizi", "Film", "Spor", "Haber", "Belgesel", "Çocuk", "Müzik", "Yaşam", "Yarışma"}

START_KEYS = ("startTime", "start", "beginTime", "startDate", "start_ts")
STOP_KEYS = ("endTime", "stop", "finishTime", "endDate", "end_ts")
TITLE_KEYS = ("title", "name", "programName", "programTitle")
DESC_KEYS = ("description", "desc", "synopsis", "summary", "shortDescription")
CAT_KEYS = ("genre", "category", "categoryName", "type")


def _to_dt(v: Any):
    """epoch(ms/s) ya da ISO string -> tz-aware (IST)."""
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)) or (isinstance(v, str) and v.isdigit()):
            ts = float(v)
            if ts > 1e12:      # ms
                ts /= 1000.0
            return datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(IST)
        dt = dtparse.parse(str(v))
        return dt.astimezone(IST) if dt.tzinfo else dt.replace(tzinfo=IST)
    except Exception:
        return None


def _looks_like_programme(d: dict) -> bool:
    has_time = any(k in d for k in START_KEYS)
    has_name = any(k in d for k in TITLE_KEYS)
    return has_time and has_name


def _pick(d: dict, keys):
    for k in keys:
        if d.get(k):
            return d[k]
    return None


def _walk(node, out: list):
    if isinstance(node, dict):
        if _looks_like_programme(node):
            out.append(node)
        for v in node.values():
            _walk(v, out)
    elif isinstance(node, list):
        for v in node:
            _walk(v, out)


class TVPlusAdapter(BaseAdapter):
    prefix = "tvplus"
    base_url = "https://tvplus.com.tr"

    def fetch(self, source_id: str, channel_id: str) -> List[Programme]:
        url = f"{self.base_url}/canli-tv/yayin-akisi/{source_id}"
        html = self._get(url).text
        progs = self._from_next_data(html, channel_id)
        if not progs:
            progs = self._from_html(html, channel_id)  # yedek
        return progs

    def _from_next_data(self, html: str, channel_id: str) -> List[Programme]:
        m = re.search(
            r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL
        )
        if not m:
            return []
        try:
            data = json.loads(m.group(1))
        except Exception:
            return []
        raw = []
        _walk(data, raw)
        out = []
        for d in raw:
            start = _to_dt(_pick(d, START_KEYS))
            if not start:
                continue
            out.append(Programme(
                channel_id=channel_id,
                start=start,
                stop=_to_dt(_pick(d, STOP_KEYS)),
                title=str(_pick(d, TITLE_KEYS) or "").strip(),
                desc=(_pick(d, DESC_KEYS) or None),
                category=(_pick(d, CAT_KEYS) or None),
                source=self.prefix,
            ))
        return out

    def _from_html(self, html: str, channel_id: str) -> List[Programme]:
        soup = BeautifulSoup(html, "lxml")
        today = ist(datetime.now())
        out: List[Programme] = []
        for li in soup.select("li.epg-card"):
            title_el = li.find("h3", class_="epg-card__title")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title:
                continue
            time_el = li.find("p", class_="epg-card__time")
            if not time_el:
                continue
            m = TIME_RANGE_RE.match(time_el.get_text(strip=True))
            if not m:
                continue
            start_dt = parse_hhmm_on(today, m.group(1))
            stop_dt = parse_hhmm_on(today, m.group(2))
            if stop_dt <= start_dt:
                stop_dt += timedelta(days=1)
            genre_el = li.find("p", class_="epg-card__genres")
            category = genre_el.get_text(strip=True) if genre_el else None
            desc_el = li.find("p", class_="epg-card__description-desktop")
            desc = desc_el.get_text(strip=True) or None if desc_el else None
            out.append(Programme(
                channel_id=channel_id,
                start=start_dt,
                stop=stop_dt,
                title=title,
                category=category,
                desc=desc,
                source=self.prefix,
            ))
        return out
