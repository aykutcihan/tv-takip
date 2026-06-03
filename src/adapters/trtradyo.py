"""
TRT Dinle radyo EPG adaptörü.
trtdinle.com kanal sayfalarından Nuxt state ile program akışını çeker.
"""
from __future__ import annotations
import json
import warnings
from datetime import datetime, timezone
from dateutil import tz

from adapters.base import BaseAdapter
from models import Programme

warnings.filterwarnings("ignore")
IST = tz.gettz("Europe/Istanbul")

# tvg-id slug -> trtdinle.com path
RADIO_CHANNELS = {
    "trt.radyo.radyo-1-radyo-programlari":            "/channel/radyo-1-radyo-programlari",
    "trt.radyo.trt-fm-turkce-pop":                    "/channel/trt-fm-turkce-pop",
    "trt.radyo.radyo-3-klasik-caz-rock-pop-ve-dunya-muzigi": "/channel/radyo-3-klasik-caz-rock-pop-ve-dunya-muzigi",
    "trt.radyo.trt-nagme-turk-sanat-muzigi":          "/channel/trt-nagme-turk-sanat-muzigi",
    "trt.radyo.trt-turku-turk-halk-muzigi":           "/channel/trt-turku-turk-halk-muzigi",
    "trt.radyo.trt-radyo-haber":                      "/channel/trt-radyo-haber",
    "trt.radyo.memleketim-fm":                        "/channel/memleketim-fm",
    "trt.radyo.turkiyenin-sesi-radyosu":              "/channel/turkiyenin-sesi-radyosu",
    "trt.radyo.trt-radyo-kurdi":                      "/channel/trt-radyo-kurdi",
    "trt.radyo.antalya-radyosu":                      "/channel/antalya-radyosu",
    "trt.radyo.cukurova-radyosu":                     "/channel/cukurova-radyosu",
    "trt.radyo.erzurum-radyosu":                      "/channel/erzurum-radyosu",
    "trt.radyo.gap-diyarbakir-radyosu":               "/channel/gap-diyarbakir-radyosu",
    "trt.radyo.trabzon-radyosu":                      "/channel/trabzon-radyosu",
}


class TRTRadyoAdapter(BaseAdapter):
    prefix = "trtradyo"

    def __init__(self, session=None):
        self._cache: dict[str, list[Programme]] = {}
        self._loaded: set[str] = set()

    def _fetch_epg(self, path: str, tvg_id: str) -> list[Programme]:
        try:
            from playwright.sync_api import sync_playwright
            programmes = []

            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
                ctx = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36"
                )
                page = ctx.new_page()
                page.goto(f"https://www.trtdinle.com{path}", wait_until="domcontentloaded", timeout=20000)
                page.wait_for_timeout(2000)

                result = page.evaluate("() => JSON.stringify(__NUXT__)")
                data = json.loads(result)

                fetch_data = data.get("fetch", {})
                epg_days = []
                for val in fetch_data.values():
                    if isinstance(val, dict) and "data" in val:
                        d = val["data"]
                        if isinstance(d, list):
                            for item in d:
                                if isinstance(item, dict) and "epg" in item:
                                    epg_days.extend(item["epg"] if isinstance(item["epg"], list) else [item])
                        elif isinstance(d, dict) and "epg" in d:
                            epg_days.extend(d["epg"])

                browser.close()

            for day_data in epg_days:
                if isinstance(day_data, dict) and "epg" in day_data:
                    for prog in day_data["epg"]:
                        try:
                            start_str = prog.get("startTime", "")
                            end_str = prog.get("endTime", "")
                            name = prog.get("name", "")
                            if not start_str or not name:
                                continue
                            start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00")).astimezone(IST)
                            if end_str:
                                end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00")).astimezone(IST)
                            else:
                                end_dt = None
                            programmes.append(Programme(
                                channel_id=tvg_id,
                                start=start_dt,
                                stop=end_dt,
                                title=name,
                            ))
                        except Exception:
                            continue

            return programmes
        except Exception as e:
            print(f"  [trtradyo] {tvg_id} hata: {e}")
            return []

    def fetch(self, source_id: str, channel_id: str) -> list[Programme]:
        if source_id not in self._loaded:
            path = RADIO_CHANNELS.get(source_id, "")
            if path:
                progs = self._fetch_epg(path, channel_id)
                self._cache[source_id] = progs
                self._loaded.add(source_id)
        return self._cache.get(source_id, [])
