"""
yayin_akisi — Show* kanallarının yayin-akisi sayfalarından EPG çeker.

Desteklenen siteler:
  showturk:  https://www.showturk.com.tr/yayin-akisi
               <a> içinde <time>HH:MM</time> + <h3>Başlık</h3>
  showmax:   https://www.showmax.com.tr/yayin-akisi
               <a> içinde "HH:MM Program Adı" düz metin

source_id = tam URL (kanaltvtr ile aynı mantık)
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
TEXT_RE = re.compile(r"^(\d{1,2}:\d{2})\s+(.+)$")


class YayinAkisiAdapter(BaseAdapter):
    prefix = "yayinakisi"

    def fetch(self, source_id: str, channel_id: str) -> List[Programme]:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                ctx = browser.new_context(locale="tr-TR")
                page = ctx.new_page()
                page.goto(source_id, wait_until="domcontentloaded", timeout=25000)
                page.wait_for_timeout(3000)
                content = page.content()
                browser.close()
        except Exception as e:
            print(f"  [yayinakisi] hata: {e}")
            return []

        if "showturk" in source_id:
            return self._parse_showturk(content, channel_id)
        if "turkhabertv" in source_id:
            return self._parse_plaintext(content, channel_id)
        return self._parse_showmax(content, channel_id)

    def _parse_showturk(self, html: str, channel_id: str) -> List[Programme]:
        soup = BeautifulSoup(html, "lxml")
        today = ist(datetime.now())
        out: List[Programme] = []
        prev_h = -1
        day_offset = 0

        for a in soup.select("a"):
            time_el = a.select_one("time")
            h3_el = a.select_one("h3")
            if not time_el or not h3_el:
                continue
            m = TIME_RE.match(time_el.get_text(strip=True))
            if not m:
                continue
            title = h3_el.get_text(strip=True)
            if not title:
                continue

            h, mn = int(m.group(1)), int(m.group(2))
            if prev_h >= 0 and h < prev_h:
                day_offset += 1
            prev_h = h

            start_dt = ist(datetime(
                today.year, today.month, today.day, h, mn
            )) + timedelta(days=day_offset)
            out.append(Programme(channel_id=channel_id, start=start_dt, title=title, source=self.prefix))

        return out

    def _parse_plaintext(self, html: str, channel_id: str) -> List[Programme]:
        """HH:MM Program Adı formatında düz metin satırları."""
        soup = BeautifulSoup(html, "lxml")
        today = ist(datetime.now())
        out: List[Programme] = []
        prev_h = -1
        day_offset = 0

        for line in soup.get_text("\n").splitlines():
            line = line.strip()
            m = TEXT_RE.match(line)
            if not m:
                continue
            time_str, title = m.group(1), m.group(2).strip()
            tm = TIME_RE.match(time_str)
            if not tm or not title:
                continue
            h, mn = int(tm.group(1)), int(tm.group(2))
            if prev_h >= 0 and h < prev_h:
                day_offset += 1
            prev_h = h
            start_dt = ist(datetime(today.year, today.month, today.day, h, mn)) + timedelta(days=day_offset)
            out.append(Programme(channel_id=channel_id, start=start_dt, title=title, source=self.prefix))

        return out

    def _parse_showmax(self, html: str, channel_id: str) -> List[Programme]:
        soup = BeautifulSoup(html, "lxml")
        today = ist(datetime.now())
        out: List[Programme] = []
        prev_h = -1
        day_offset = 0

        for a in soup.select("a"):
            text = a.get_text(" ", strip=True)
            m = TEXT_RE.match(text)
            if not m:
                continue
            time_str, title = m.group(1), m.group(2).strip()
            tm = TIME_RE.match(time_str)
            if not tm:
                continue

            h, mn = int(tm.group(1)), int(tm.group(2))
            if prev_h >= 0 and h < prev_h:
                day_offset += 1
            prev_h = h

            start_dt = ist(datetime(
                today.year, today.month, today.day, h, mn
            )) + timedelta(days=day_offset)
            out.append(Programme(channel_id=channel_id, start=start_dt, title=title, source=self.prefix))

        return out
