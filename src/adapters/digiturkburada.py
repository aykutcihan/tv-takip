"""
digiturkburada (digiturkburada.com.tr) — beIN YEDEĞİ.

URL: https://www.digiturkburada.com.tr/{slug-id}.html
     örn: bein-sports-1-hd-yayin-akisi-60
Tablo: ad + başlangıç (BİTİŞ/AÇIKLAMA YOK). Aynı link günlük yenilenir; 3 gün ayrı linklerde.

>>> CANLI HTML'E GÖRE AYAR GEREKEBİLİR <<<
Tablo satır selector'ını (saat hücresi + ad hücresi) PC'de doğrula.
3 günlük link yapısı (göreli mi tarih damgalı mı) netleşince çoklu-gün eklenir.
"""
from __future__ import annotations
import re
from datetime import datetime
from typing import List

from bs4 import BeautifulSoup

from adapters.base import BaseAdapter
from models import Programme
from normalize import parse_hhmm_on, simplify, ist

TIME_RE = re.compile(r"(\d{1,2}):(\d{2})")


class DigiturkBuradaAdapter(BaseAdapter):
    prefix = "digiturkburada"
    base_url = "https://www.digiturkburada.com.tr"

    def fetch(self, source_id: str, channel_id: str) -> List[Programme]:
        url = f"{self.base_url}/{source_id}.html"
        html = self._get(url).text
        return self._parse(html, channel_id)

    def _parse(self, html: str, channel_id: str) -> List[Programme]:
        soup = BeautifulSoup(html, "lxml")
        soup.encoding = "utf-8"
        today = ist(datetime.now())
        out: List[Programme] = []
        # Tablo: <tr><td>Yayın İsmi</td><td>Başlangıç</td></tr>
        for row in soup.select("tr"):
            cells = row.select("td")
            if len(cells) < 2:
                continue
            name = cells[0].get_text(strip=True)
            time_txt = cells[1].get_text(strip=True)
            mt = TIME_RE.match(time_txt)
            if not mt or not name:
                continue
            hhmm = f"{mt.group(1)}:{mt.group(2)}"
            s = simplify(name)
            out.append(Programme(
                channel_id=channel_id,
                start=parse_hhmm_on(today, hhmm),
                title=s["title"], desc=s["desc"], category="Spor",
                source=self.prefix,
            ))
        return out
