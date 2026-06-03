"""
dosttv (dosttv.com) — Günlük yayın akışı, requests ile.

URL: https://dosttv.com/yayin-akisi/
Yapı: <table> içinde <tr> satırları, her satırda saat + başlık + açıklama.
Sabit günlük program, döngüyle tekrar.
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


class DostTvAdapter(BaseAdapter):
    prefix = "dosttv"
    URL = "https://dosttv.com/yayin-akisi/"

    def __init__(self, session=None, delay: float = 0.2):
        super().__init__(session, delay)
        self._progs: list = []
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
            print(f"  [dosttv] hata: {e}")
            return

        soup = BeautifulSoup(r.text, "lxml")
        table = soup.find("table")
        if not table:
            return

        # Satır bazlı parse
        for row in table.select("tr"):
            cells = [td.get_text(strip=True) for td in row.select("td")]
            if not cells:
                continue
            # Saat hücresini bul
            m = None
            for i, c in enumerate(cells):
                m = TIME_RE.match(c)
                if m:
                    h, mn = int(m.group(1)), int(m.group(2))
                    # Başlık sonraki hücrede
                    raw = cells[i + 1] if i + 1 < len(cells) else ""
                    # Açıklama başlıkla aynı hücrede olabilir — ilk cümle başlık
                    # veya ayrı hücrede
                    desc_raw = cells[i + 2] if i + 2 < len(cells) else ""
                    if not desc_raw and len(raw) > 40:
                        # Başlık + açıklama birleşik — ilk büyük harften böl
                        sp = re.split(r'(?<=[a-zçğıöşü])(?=[A-ZÇĞİÖŞÜ])', raw, maxsplit=1)
                        title = sp[0].strip()
                        desc = sp[1].strip() if len(sp) > 1 else ""
                    else:
                        title = raw
                        desc = desc_raw
                    if title:
                        self._progs.append((h, mn, title, desc or None))
                    break

        print(f"  [dosttv] {len(self._progs)} program yüklendi")

    def _generate(self, channel_id: str) -> List[Programme]:
        if not self._progs:
            return []

        today = ist(datetime.now())
        out: List[Programme] = []

        for offset in range(-7, 22):
            day_base = today + timedelta(days=offset)
            for h, mn, title, desc in self._progs:
                start_dt = ist(datetime(day_base.year, day_base.month, day_base.day, h, mn))
                out.append(Programme(
                    channel_id=channel_id,
                    start=start_dt,
                    title=title,
                    desc=desc,
                    source=self.prefix,
                ))
        return out
