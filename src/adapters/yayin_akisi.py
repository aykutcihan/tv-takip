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
TEXT_RE = re.compile(r"^(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)$")


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
        if "turkhabertv" in source_id or "tv41" in source_id:
            return self._parse_plaintext(content, channel_id)
        if "turkuvapp" in source_id:
            return self._parse_turkuvapp(content, channel_id)
        if "kontv" in source_id:
            return self._parse_kontv(content, channel_id)
        if "kanalb" in source_id:
            return self._parse_kanalb(content, channel_id)
        return self._parse_showmax(content, channel_id)

    def _parse_showturk(self, html: str, channel_id: str) -> List[Programme]:
        soup = BeautifulSoup(html, "lxml")
        today = ist(datetime.now())
        out: List[Programme] = []
        prev_h = -1
        day_offset = 0

        for a in soup.select("a"):
            divs = a.find_all("div", recursive=False)
            # time ve h3 veya iki div (biri saat biri baslik)
            time_el = a.select_one("time") or (divs[0] if divs else None)
            title_el = a.select_one("h3") or (divs[-1] if len(divs) >= 2 else None)
            if not time_el or not title_el or time_el is title_el:
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
            out.append(Programme(channel_id=channel_id, start=start_dt, title=title, source=self.prefix))

        return out

    def _parse_kontv(self, html: str, channel_id: str) -> List[Programme]:
        """<h3>HH:MM</h3> sonrasi metin baslik."""
        soup = BeautifulSoup(html, "lxml")
        today = ist(datetime.now())
        out: List[Programme] = []
        prev_h = -1
        day_offset = 0

        for h3 in soup.find_all("h3"):
            m = TIME_RE.match(h3.get_text(strip=True))
            if not m:
                continue
            title = h3.next_sibling
            if title:
                title = str(title).strip().lstrip("\n").strip()
            if not title:
                continue
            h, mn = int(m.group(1)), int(m.group(2))
            if prev_h >= 0 and h < prev_h:
                day_offset += 1
            prev_h = h
            start_dt = ist(datetime(today.year, today.month, today.day, h, mn)) + timedelta(days=day_offset)
            out.append(Programme(channel_id=channel_id, start=start_dt, title=title, source=self.prefix))
        return out

    def _parse_kanalb(self, html: str, channel_id: str) -> List[Programme]:
        """<li><a><span class='time'>HH:MM</span> Baslik</a></li>"""
        soup = BeautifulSoup(html, "lxml")
        today = ist(datetime.now())
        out: List[Programme] = []
        prev_h = -1
        day_offset = 0

        for li in soup.select("li"):
            span = li.select_one(".time, span[class*='time']")
            if not span:
                continue
            m = TIME_RE.match(span.get_text(strip=True))
            if not m:
                continue
            span.extract()
            a = li.select_one("a")
            title = (a or li).get_text(strip=True) if (a or li) else ""
            if not title:
                continue
            h, mn = int(m.group(1)), int(m.group(2))
            if prev_h >= 0 and h < prev_h:
                day_offset += 1
            prev_h = h
            start_dt = ist(datetime(today.year, today.month, today.day, h, mn)) + timedelta(days=day_offset)
            out.append(Programme(channel_id=channel_id, start=start_dt, title=title, source=self.prefix))
        return out

    def _parse_turkuvapp(self, html: str, channel_id: str) -> List[Programme]:
        """<li><a>HH:MMBaşlık</a></li> formatı."""
        soup = BeautifulSoup(html, "lxml")
        today = ist(datetime.now())
        out: List[Programme] = []
        prev_h = -1
        day_offset = 0

        for li in soup.select("li"):
            a = li.select_one("a")
            if not a:
                continue
            text = a.get_text(strip=True)
            m = re.match(r'^(\d{1,2}:\d{2})\s*(.+)$', text)
            if not m:
                continue
            tm = TIME_RE.match(m.group(1))
            title = m.group(2).strip()
            if not tm or not title:
                continue

            h, mn = int(tm.group(1)), int(tm.group(2))
            if prev_h >= 0 and h < prev_h:
                day_offset += 1
            prev_h = h
            start_dt = ist(datetime(today.year, today.month, today.day, h, mn)) + timedelta(days=day_offset)
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
