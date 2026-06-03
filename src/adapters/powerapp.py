"""
powerapp (powerapp.com.tr) — Power TV kanalları yayın akışı.

URL: https://www.powerapp.com.tr/tvs/power-tvs/{slug}/
Yapı: .schedule .info > .name (saat) + .artist (program adı)
Playwright gerekiyor (JS rendered).
"""
from __future__ import annotations
import re
from datetime import datetime, timedelta
from typing import List, Dict

from bs4 import BeautifulSoup

from adapters.base import BaseAdapter
from models import Programme
from normalize import ist

TIME_RE = re.compile(r"(\d{1,2}):(\d{2})")


class PowerAppAdapter(BaseAdapter):
    prefix = "powerapp"
    base_url = "https://www.powerapp.com.tr/tvs/power-tvs"

    def __init__(self, session=None, delay: float = 0.5):
        super().__init__(session, delay)
        self._cache: Dict[str, list] = {}
        self._loaded: set = set()

    def fetch(self, source_id: str, channel_id: str) -> List[Programme]:
        if source_id not in self._loaded:
            self._load(source_id)
        return self._generate(source_id, channel_id)

    def _load(self, slug: str):
        self._loaded.add(slug)
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return

        url = f"{self.base_url}/{slug}/"
        content = ""
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
                    )
                )
                ctx.add_init_script(
                    'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
                )
                page = ctx.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=25000)
                page.wait_for_timeout(5000)
                content = page.content()
                browser.close()
        except Exception as e:
            print(f"  [powerapp] {slug} hata: {e}")
            return

        soup = BeautifulSoup(content, "lxml")
        progs = []
        seen = set()
        for info in soup.select(".schedule .info, [class*=schedule] .info"):
            name_el = info.select_one(".name")
            artist_el = info.select_one(".artist")
            if not name_el or not artist_el:
                continue
            time_txt = name_el.get_text(strip=True)
            title = artist_el.get_text(strip=True)
            m = TIME_RE.match(time_txt)
            if not m or not title:
                continue
            key = (int(m.group(1)), int(m.group(2)), title)
            if key not in seen:
                seen.add(key)
                progs.append((int(m.group(1)), int(m.group(2)), title))

        self._cache[slug] = progs
        print(f"  [powerapp] {slug}: {len(progs)} program")

    def _generate(self, slug: str, channel_id: str) -> List[Programme]:
        progs = self._cache.get(slug, [])
        if not progs:
            return []

        today = ist(datetime.now())
        out: List[Programme] = []

        for offset in range(-7, 22):
            day_base = today + timedelta(days=offset)
            for h, m, title in progs:
                start_dt = ist(datetime(day_base.year, day_base.month, day_base.day, h, m))
                out.append(Programme(
                    channel_id=channel_id,
                    start=start_dt,
                    title=title,
                    source=self.prefix,
                ))
        return out
