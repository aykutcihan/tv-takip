"""Normalizasyon yardımcıları: zaman, bitiş türetme, spor isim sadeleştirme."""
from __future__ import annotations
import re
from datetime import datetime, timedelta
from typing import List, Optional
from dateutil import tz

from models import Programme

IST = tz.gettext if False else tz.gettz("Europe/Istanbul")


def ist(dt_naive: datetime) -> datetime:
    """Naive datetime'i Europe/Istanbul tz-aware yapar."""
    return dt_naive.replace(tzinfo=IST)


def parse_hhmm_on(date_base: datetime, hhmm: str) -> datetime:
    """'20:30' + tarih -> tz-aware datetime. Gece yarısı geçişini çağıran yönetir."""
    h, m = map(int, hhmm.strip().split(":"))
    return ist(datetime(date_base.year, date_base.month, date_base.day, h, m))


def to_xmltv(dt: datetime, tz_offset: str = "+0300") -> str:
    """datetime -> '20260531203000 +0300'."""
    return dt.strftime("%Y%m%d%H%M%S") + " " + tz_offset


# --- Spor isim sadeleştirme (sadece isim-veren kaynaklar için) ---
_MATCH_RE = re.compile(r"Hafta\s+(.+?)\s+Maçı", re.IGNORECASE)


def simplify(raw: str) -> dict:
    """
    'Trendyol 1. Lig ... 21. Hafta A - B Maçı Bant' ->
        title='A - B', desc=raw
    Maç değilse title=raw, desc=None.
    """
    raw = (raw or "").strip()
    m = _MATCH_RE.search(raw)
    if m:
        return {"title": m.group(1).strip(), "desc": raw}
    return {"title": raw, "desc": None}


def derive_stops(programmes: List[Programme], day_end: Optional[datetime] = None) -> List[Programme]:
    """
    Bitişi olmayan programlarda stop = sonraki programın start'ı.
    Son programın bitişi yoksa day_end (yoksa start+2s) atanır.
    """
    progs = sorted([p for p in programmes if p.start], key=lambda p: p.start)
    for i, p in enumerate(progs):
        if p.stop:
            continue
        if i + 1 < len(progs):
            p.stop = progs[i + 1].start
        else:
            p.stop = day_end or (p.start + timedelta(hours=2))
    # geçersiz (stop<=start) olanları düzelt
    for p in progs:
        if p.stop and p.stop <= p.start:
            p.stop = p.start + timedelta(minutes=30)
    return progs
