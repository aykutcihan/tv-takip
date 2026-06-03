"""
kanaltvtr — Playwright ile kanal sitelerinden yayın akışı.

Desteklenen siteler (schedule-content yapısı):
  kanal7avrupa: https://www.kanal7avrupa.com/yayin-akisi

HTML yapısı:
  <div class="schedule-content">
    <div class="time">06:00</div>
    <div class="info">
      <div class="title">Program Adı</div>
      <div class="category">Kategori</div>
    </div>
  </div>
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


class KanalTvTrAdapter(BaseAdapter):
    prefix = "kanaltvtr"

    def fetch(self, source_id: str, channel_id: str) -> List[Programme]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return []

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
                page.goto(source_id, wait_until="domcontentloaded", timeout=25000)
                page.wait_for_timeout(4000)
                content = page.content()
                browser.close()
        except Exception as e:
            print(f"  [kanaltvtr] hata: {e}")
            return []

        return self._parse(content, channel_id)

    def _parse(self, html: str, channel_id: str) -> List[Programme]:
        soup = BeautifulSoup(html, "lxml")
        today = ist(datetime.now())
        out: List[Programme] = []
        prev_h = -1
        day_offset = 0

        for block in soup.select(".schedule-content"):
            time_el = block.select_one(".time")
            title_el = block.select_one(".title")
            cat_el = block.select_one(".category")

            if not time_el or not title_el:
                continue
            m = TIME_RE.match(time_el.get_text(strip=True))
            if not m:
                continue
            title = title_el.get_text(strip=True)
            if not title:
                continue

            h, mn = int(m.group(1)), int(m.group(2))
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
                category=cat_el.get_text(strip=True) if cat_el else None,
                source=self.prefix,
            ))
        return out
