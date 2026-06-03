"""
canlitv (tr.canlitv.watch) — kanal bazlı yayın akışı.

URL: https://tr.canlitv.watch/{slug}
Yapı: <li><span>HH:MM</span><b>Program Adı</b></li>
Sadece başlangıç saati var, bitiş derive_stops ile türetilir.
"""
from __future__ import annotations
import re
from datetime import datetime, timedelta
from typing import List

from bs4 import BeautifulSoup

from adapters.base import BaseAdapter
from models import Programme
from normalize import ist

TIME_RE = re.compile(r"(\d{1,2}):(\d{2})")


class CanliTvAdapter(BaseAdapter):
    prefix = "canlitv"
    base_url = "https://tr.canlitv.watch"

    def fetch(self, source_id: str, channel_id: str) -> List[Programme]:
        url = f"{self.base_url}/{source_id}"
        html = self._get(url).text
        return self._parse(html, channel_id)

    def _parse(self, html: str, channel_id: str) -> List[Programme]:
        soup = BeautifulSoup(html, "lxml")
        today = ist(datetime.now())
        out: List[Programme] = []
        prev_h = -1
        day_offset = 0

        for li in soup.select("li"):
            span = li.find("span")
            bold = li.find("b")
            if not span or not bold:
                continue
            m = TIME_RE.match(span.get_text(strip=True))
            if not m:
                continue
            title = bold.get_text(strip=True)
            if not title:
                continue
            h, mn = int(m.group(1)), int(m.group(2))
            # Gece yarısı geçişi
            if prev_h >= 0 and h < prev_h:
                day_offset += 1
            prev_h = h
            start_dt = ist(datetime(
                today.year, today.month, today.day, h, mn
            )) + timedelta(days=day_offset)
            out.append(Programme(
                channel_id=channel_id,
                start=start_dt,
                title=title,
                source=self.prefix,
            ))
        return out
