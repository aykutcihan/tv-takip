"""
Tivibu (tivibu.com.tr) — Playwright ile canli-tv sayfasindan program verisi.

Site JavaScript gerektirdiği için requests ile çalışmıyor.
Tek Playwright oturumunda tüm kanallar yüklenir ve önbelleğe alınır;
her fetch() çağrısı bu önbellekten kanal ID'sine göre veri döndürür.
"""
from __future__ import annotations
import re
from datetime import datetime, timedelta
from typing import List, Dict
from urllib.parse import unquote

from bs4 import BeautifulSoup

from adapters.base import BaseAdapter
from models import Programme
from normalize import ist

CH_RE = re.compile(r"ch[0-9a-f]{20}", re.IGNORECASE)
TIME_RE = re.compile(r"(\d{1,2}):(\d{2})")


class TivibuAdapter(BaseAdapter):
    prefix = "tivibu"
    base_url = "https://www.tivibu.com.tr"

    def __init__(self, session=None, delay: float = 0.2):
        super().__init__(session, delay)
        self._cache: Dict[str, List[Programme]] = {}
        self._loaded = False

    def fetch(self, source_id: str, channel_id: str) -> List[Programme]:
        if not self._loaded:
            self._fill_cache()
        return [Programme(
            channel_id=channel_id,
            start=p.start, stop=p.stop,
            title=p.title, category=p.category,
            source=self.prefix,
        ) for p in self._cache.get(source_id, [])]

    def _fill_cache(self):
        self._loaded = True
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("  [tivibu] playwright kurulu degil, atlaniyor.")
            return

        # Her kategori sayfasi ayri URL'e sahip
        CATEGORY_PATHS = [
            "/canli-tv/",
            "/canli-tv/spor",
            "/canli-tv/muzik",
            "/canli-tv/ulusal",
            "/canli-tv/haber",
            "/canli-tv/dizi",
            "/canli-tv/belgesel",
            "/canli-tv/cocuk",
            "/canli-tv/yasam-stil",
            "/canli-tv/global",
            "/canli-tv/sinema",
        ]
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
                )
                ctx = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/125.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1366, "height": 768},
                )
                ctx.add_init_script(
                    'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
                )
                page = ctx.new_page()
                for path in CATEGORY_PATHS:
                    for attempt in range(2):  # max 2 deneme
                        try:
                            page.goto(
                                f"{self.base_url}{path}",
                                wait_until="networkidle",
                                timeout=40000,
                            )
                            self._parse_page(page.content())
                            break
                        except Exception as e:
                            if attempt == 0:
                                print(f"  [tivibu] {path} yeniden deneniyor...")
                            else:
                                print(f"  [tivibu] {path} hatasi: {e}")
                browser.close()
        except Exception as e:
            print(f"  [tivibu] Playwright hatasi: {e}")
            return
        total = sum(len(v) for v in self._cache.values())
        print(f"  [tivibu] {len(self._cache)} kanal, {total} program önbelleğe alındı.")

    def _parse_page(self, content: str):
        soup = BeautifulSoup(content, "lxml")
        today = ist(datetime.now())

        for box in soup.select(".programBox"):
            link = box.find("a", href=True)
            if not link:
                continue
            m = CH_RE.search(unquote(link["href"]))
            if not m:
                continue
            ch_id = m.group(0)

            title_el = box.find(class_="programTitle")
            type_el = box.find(class_="type")
            start_el = box.find(class_="startTime")
            stop_el = box.find(class_="finishTime")

            title = title_el.get_text(strip=True) if title_el else ""
            category = type_el.get_text(strip=True) if type_el else None
            start_txt = start_el.get_text(strip=True) if start_el else ""
            stop_txt = stop_el.get_text(strip=True) if stop_el else ""

            if not title or not start_txt:
                continue

            ms = TIME_RE.match(start_txt)
            if not ms:
                continue
            start_dt = ist(datetime(today.year, today.month, today.day,
                                    int(ms.group(1)), int(ms.group(2))))

            stop_dt = None
            me = TIME_RE.match(stop_txt)
            if me:
                stop_dt = ist(datetime(today.year, today.month, today.day,
                                       int(me.group(1)), int(me.group(2))))
                if stop_dt <= start_dt:
                    stop_dt += timedelta(days=1)

            self._cache.setdefault(ch_id, []).append(Programme(
                channel_id=ch_id,
                start=start_dt,
                stop=stop_dt,
                title=title,
                category=category,
                source=self.prefix,
            ))
