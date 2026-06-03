"""
tvyayinakisi.com — Tek istekte tüm kanallar.

URL: https://www.tvyayinakisi.com/tvde-bugun-rehberi/
Yapı: div.channels-today__program[data-channel-slug] kapsayıcısı içinde
      div.channels-today__program__item elementleri (başlık + saat aralığı).

Avantajlar (eski adaptöre göre):
- Tek HTTP isteği → 50 kanal
- Başlangıç VE bitiş saati mevcut
- Temiz class-based selector, fragile regex yok
"""
from __future__ import annotations
import re
from datetime import datetime, timedelta
from typing import List, Dict

from bs4 import BeautifulSoup

from adapters.base import BaseAdapter
from models import Programme
from normalize import ist, simplify

TIME_RANGE_RE = re.compile(r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})")
TIME_RE = re.compile(r"(\d{1,2})\s*:\s*(\d{2})")
CAT_RE = re.compile(r"\b(Spor|Dizi|Film|Belgesel|Haber|Çocuk|Müzik)\b$")
FILLER = ("az sonra", "yayın akışı bulunamadı", "bu gün için")


class TvYayinAkisiAdapter(BaseAdapter):
    prefix = "tvyayinakisi"
    base_url = "https://www.tvyayinakisi.com"

    def __init__(self, session=None, delay: float = 0.2):
        super().__init__(session, delay)
        self._cache: Dict[str, List[Programme]] = {}
        self._loaded = False

    def fetch(self, source_id: str, channel_id: str) -> List[Programme]:
        if not self._loaded:
            self._fill_cache()
        if source_id in self._cache:
            raw = self._cache[source_id]
            return [Programme(
                channel_id=channel_id,
                start=p.start, stop=p.stop,
                title=p.title, category=p.category,
                source=self.prefix,
            ) for p in raw]
        # Guide'da yok — bireysel kanal sayfasını dene (eski <li><strong> yapısı)
        return self._fetch_individual(source_id, channel_id)

    def _fill_cache(self):
        self._loaded = True
        try:
            html = self._get(f"{self.base_url}/tvde-bugun-rehberi/").text
        except Exception as e:
            print(f"  [tvyayinakisi] istek hatasi: {e}")
            return
        self._parse_page(html)
        total = sum(len(v) for v in self._cache.values())
        print(f"  [tvyayinakisi] {len(self._cache)} kanal, {total} program önbelleğe alındı.")

    def _fetch_individual(self, slug: str, channel_id: str) -> List[Programme]:
        """Bireysel kanal sayfası: <li><strong>HH</strong>:MM Başlık [Kategori]"""
        try:
            html = self._get(f"{self.base_url}/{slug}-yayin-akisi/").text
        except Exception:
            return []
        soup = BeautifulSoup(html, "lxml")
        today = ist(datetime.now())
        out: List[Programme] = []
        for li in soup.select("li"):
            if not li.find("strong"):
                continue
            txt = " ".join(li.get_text("").split())
            if not txt or any(f in txt.lower() for f in FILLER):
                continue
            mt = TIME_RE.search(txt)
            if not mt:
                continue
            hhmm = f"{mt.group(1)}:{mt.group(2)}"
            rest = txt[mt.end():].strip(" -–—")
            if not rest:
                continue
            cm = CAT_RE.search(rest)
            category = cm.group(1) if cm else None
            raw_title = rest[:cm.start()].strip() if cm else rest
            # Spor kanalları: "21. Hafta A - B Maçı" → title="A - B", desc=full
            s = simplify(raw_title) if category and category.lower() == "spor" else {"title": raw_title, "desc": None}
            try:
                h, m = int(mt.group(1)), int(mt.group(2))
                start_dt = ist(datetime(today.year, today.month, today.day, h % 24, m))
                if h >= 24:
                    start_dt += timedelta(days=1)
            except ValueError:
                continue
            out.append(Programme(
                channel_id=channel_id,
                start=start_dt,
                title=s["title"], desc=s["desc"], category=category,
                source=self.prefix,
            ))
        return out

    def _parse_page(self, html: str):
        soup = BeautifulSoup(html, "lxml")
        today = ist(datetime.now())

        for ch_div in soup.select("div.channels-today__program[data-channel-slug]"):
            slug_full = ch_div.get("data-channel-slug", "")
            slug = slug_full.replace("-yayin-akisi", "")

            progs: List[Programme] = []
            for item in ch_div.select("div.channels-today__program__item"):
                title_el = item.select_one(".channels-today__program__title")
                time_el = item.select_one(".channels-today__program__time")

                title = title_el.get_text(strip=True) if title_el else ""
                time_txt = time_el.get_text("").replace(" ", "") if time_el else ""

                m = TIME_RANGE_RE.search(time_txt)
                if not m or not title:
                    continue

                sh, sm, eh, em = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
                # 24:XX → ertesi günün 0:XX
                start_dt = ist(datetime(today.year, today.month, today.day, sh % 24, sm))
                stop_dt = ist(datetime(today.year, today.month, today.day, eh % 24, em))
                if sh >= 24:
                    start_dt += timedelta(days=1)
                if eh >= 24 or stop_dt <= start_dt:
                    stop_dt += timedelta(days=1)

                progs.append(Programme(
                    channel_id="",  # fetch() içinde doğru id ile üretilir
                    start=start_dt,
                    stop=stop_dt,
                    title=title,
                    source=self.prefix,
                ))

            if progs:
                self._cache[slug] = progs
