"""
gurbet24 (gurbet24.com) — Haftalık yayın akışı.

URL: https://www.gurbet24.com/index.php/yayin-akisi
Yapı: Her program ayrı <table> içinde, <tr><td>HH:MM</td><td></td><td>Başlık</td></tr>
Sabit haftalık program, 5 gün (Pzt-Cuma). Döngüyle tekrar.
"""
from __future__ import annotations
import re
from datetime import datetime, timedelta
from typing import List

import requests
from bs4 import BeautifulSoup

from adapters.base import BaseAdapter
from models import Programme
from normalize import ist

TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})$")


class Gurbet24Adapter(BaseAdapter):
    prefix = "gurbet24"
    URL = "https://www.gurbet24.com/index.php/yayin-akisi"

    def __init__(self, session=None, delay: float = 0.2):
        super().__init__(session, delay)
        self._days: list = []
        self._loaded = False

    def fetch(self, source_id: str, channel_id: str) -> List[Programme]:
        if not self._loaded:
            self._load()
        return self._generate(channel_id)

    def _load(self):
        self._loaded = True
        try:
            r = self._get(self.URL)
            r.encoding = "utf-8"
        except Exception as e:
            print(f"  [gurbet24] hata: {e}")
            return

        soup = BeautifulSoup(r.text, "lxml")
        # Her program ayrı tabloda
        progs_raw = []
        for t in soup.find_all("table"):
            row = t.find("tr")
            if not row:
                continue
            cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
            if not cells:
                continue
            m = TIME_RE.match(cells[0])
            if not m:
                continue
            # Başlık 3. sütunda, yoksa son sütunda
            title = cells[2] if len(cells) > 2 else (cells[-1] if cells else "")
            # CANLI YAYIN prefix'ini temizle
            title = re.sub(r"^CANLI\s*YAYIN\s*", "", title).strip()
            if not title:
                continue
            progs_raw.append((int(m.group(1)), int(m.group(2)), title))

        # Günlere böl: her 00:00 yeni gün başlangıcı
        current_day = []
        for h, m, title in progs_raw:
            if h == 0 and m == 0 and current_day:
                self._days.append(current_day)
                current_day = []
            current_day.append((h, m, title))
        if current_day:
            self._days.append(current_day)

        print(f"  [gurbet24] {len(self._days)} gün, {len(progs_raw)} program yüklendi")

    def _generate(self, channel_id: str) -> List[Programme]:
        if not self._days:
            return []

        today = ist(datetime.now())
        out: List[Programme] = []
        n_days = len(self._days)

        # 4 haftalık veri üret
        for offset in range(-7, 22):
            day_base = today + timedelta(days=offset)
            day_progs = self._days[day_base.weekday() % n_days]
            for h, m, title in day_progs:
                start_dt = ist(datetime(day_base.year, day_base.month, day_base.day, h, m))
                out.append(Programme(
                    channel_id=channel_id,
                    start=start_dt,
                    title=title,
                    source=self.prefix,
                ))
        return out
