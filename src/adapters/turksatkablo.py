"""
turksatkablo (turksatkablo.com.tr) — JSON EPG API.

URL: https://www.turksatkablo.com.tr/userUpload/EPG/{gün}.json
     gün 1=bugün, 2=yarın, ..., 7=7 gün sonra

Yapı: {"k": [{"i": id, "n": "Kanal Adı", "p": [{"a": id, "b": "Başlık", "c": "HH:MM", "d": "HH:MM"}, ...]}, ...]}

Tek istekte 179 kanal, başlangıç + bitiş saati. SSL sertifika sorunu var, verify=False.
source_id = Türksat kanal adı (channels.yaml'daki name ile eşleşir)
"""
from __future__ import annotations
import re
from datetime import datetime, timedelta
from typing import List, Optional
import urllib3

from adapters.base import BaseAdapter
from models import Programme
from normalize import ist

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TIME_RE = re.compile(r"(\d{1,2}):(\d{2})")


class TurksatKabloAdapter(BaseAdapter):
    prefix = "turksatkablo"
    base_url = "https://www.turksatkablo.com.tr/userUpload/EPG"

    def __init__(self, session=None, delay: float = 0.2):
        super().__init__(session, delay)
        self._cache: dict = {}   # {kanal_adi: {day_offset: [Programme]}}
        self._loaded_days: set = set()

    def fetch(self, source_id: str, channel_id: str) -> List[Programme]:
        # source_id = Türksat kanal adı (örn. "Sinema TV")
        all_progs = []
        for day in range(1, 8):
            if day not in self._loaded_days:
                self._load_day(day)
            progs = self._cache.get(source_id, {}).get(day, [])
            for p in progs:
                all_progs.append(Programme(
                    channel_id=channel_id,
                    start=p.start, stop=p.stop,
                    title=p.title, source=self.prefix,
                ))
        return all_progs

    def _load_day(self, day: int):
        self._loaded_days.add(day)
        try:
            r = self.s.get(
                f"{self.base_url}/{day}.json",
                timeout=20,
                verify=False,
                headers={"Referer": "https://www.turksatkablo.com.tr/yayin-akisi.aspx"},
            )
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"  [turksatkablo] gün {day} hata: {e}")
            return

        today = ist(datetime.now())
        # 1.json = bugün (today+0), 2.json = yarın (today+1), ...
        day_base = today + timedelta(days=day - 1)

        for ch in data.get("k", []):
            ch_name = ch.get("n", "").strip()
            ch_id = ch.get("i")
            if not ch_name:
                continue
            progs = []
            for p in ch.get("p", []):
                title = (p.get("b") or "").strip()
                if not title or title == "-":
                    continue
                ms = TIME_RE.match(p.get("c", ""))
                me = TIME_RE.match(p.get("d", ""))
                if not ms or not me:
                    continue
                sh, sm = int(ms.group(1)), int(ms.group(2))
                eh, em = int(me.group(1)), int(me.group(2))
                start_dt = ist(datetime(day_base.year, day_base.month, day_base.day, sh, sm))
                stop_dt = ist(datetime(day_base.year, day_base.month, day_base.day, eh, em))
                if stop_dt <= start_dt:
                    stop_dt += timedelta(days=1)
                progs.append(Programme(
                    channel_id=ch_name,
                    start=start_dt,
                    stop=stop_dt,
                    title=title,
                    source=self.prefix,
                ))

            if ch_name not in self._cache:
                self._cache[ch_name] = {}
            self._cache[ch_name][day] = progs

        print(f"  [turksatkablo] gün {day}: {len(data.get('k', []))} kanal yüklendi")
