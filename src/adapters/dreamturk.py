"""
dreamturk (dreamturk.com.tr) — Haftalık yayın akışı, requests ile.

URL: https://www.dreamturk.com.tr/yayin-akisi
Yapı: <li><div class="hour">HH:MM</div><div class="desc"><a>Başlık</a></div></li>
Haftalık program, her 07:00 yeni gün başlangıcı.
"""
from __future__ import annotations
import re
from datetime import datetime, timedelta
from typing import List

from bs4 import BeautifulSoup

from adapters.base import BaseAdapter
from models import Programme
from normalize import ist

TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})$")


class DreamTurkAdapter(BaseAdapter):
    prefix = "dreamturk"
    URL = "https://www.dreamturk.com.tr/yayin-akisi"

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
            print(f"  [dreamturk] hata: {e}")
            return

        soup = BeautifulSoup(r.text, "lxml")
        current_day = []

        for li in soup.select("li"):
            hour_el = li.select_one(".hour")
            desc_el = li.select_one(".desc a:last-child")
            if not hour_el or not desc_el:
                continue
            time_txt = hour_el.get_text(strip=True)
            title = desc_el.get_text(strip=True)
            if not title or title in ("CANLI İZLE", "Canlı İzle"):
                continue
            m = TIME_RE.match(time_txt)
            if not m:
                continue
            h, mn = int(m.group(1)), int(m.group(2))
            # 07:00 yeni gün başlangıcı (önceki gün varsa kaydet)
            if h == 7 and mn == 0 and current_day:
                self._days.append(current_day)
                current_day = []
            current_day.append((h, mn, title))

        if current_day:
            self._days.append(current_day)

        print(f"  [dreamturk] {len(self._days)} gün, {sum(len(d) for d in self._days)} program yüklendi")

    def _generate(self, channel_id: str) -> List[Programme]:
        if not self._days:
            return []

        today = ist(datetime.now())
        out: List[Programme] = []
        n_days = len(self._days)

        for offset in range(-7, 22):
            day_base = today + timedelta(days=offset)
            day_progs = self._days[day_base.weekday() % n_days]
            for h, mn, title in day_progs:
                start_dt = ist(datetime(day_base.year, day_base.month, day_base.day, h, mn))
                out.append(Programme(
                    channel_id=channel_id,
                    start=start_dt,
                    title=title,
                    source=self.prefix,
                ))
        return out
