"""
Token tabanlı stream URL'lerini yenile.
Playlist.m3u'daki işaretli kanallar için taze token alır.

Çalıştır: python src/refresh_tokens.py
"""
from __future__ import annotations
import re
import sys
import urllib.parse
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
PLAYLIST = ROOT / "playlist.m3u"

# tvg-id → (channel_id, base_url)  — token API parametreleri
TOKEN_CHANNELS = {
    "tr.aspor":    (28008,  "https://trkvz-live.ercdn.net/asporhd/asporhd.m3u8"),
    "tr.apara":    (379515, "https://trkvz-live.ercdn.net/aparahd/aparahd.m3u8"),
    # ATV, A Haber, A2, ATV Avrupa - ID'ler bulunamadi, manuel ekleniyor
}

TOKEN_API = "https://securevideotoken.tmgrup.com.tr/webtv/secure"


def get_token_url(ch_id: int, base_url: str) -> str | None:
    encoded = urllib.parse.quote(base_url, safe="")
    url = f"{TOKEN_API}?{ch_id}&url={encoded}"
    try:
        r = requests.get(url, timeout=10,
                         headers={"User-Agent": "Mozilla/5.0",
                                  "Referer": "https://www.atv.com.tr/"})
        data = r.json()
        return data.get("Url") or None
    except Exception as e:
        print(f"  [token] hata: {e}")
        return None


def main():
    content = PLAYLIST.read_text(encoding="utf-8")
    lines = content.splitlines()
    updated = 0

    for i, line in enumerate(lines):
        if not line.startswith("#EXTINF:"):
            continue
        m = re.search(r'tvg-id="([^"]+)"', line)
        if not m:
            continue
        tvg_id = m.group(1)
        if tvg_id not in TOKEN_CHANNELS:
            continue

        ch_id, base_url = TOKEN_CHANNELS[tvg_id]
        token_url = get_token_url(ch_id, base_url)
        if token_url and i + 1 < len(lines):
            lines[i + 1] = token_url
            updated += 1
            print(f"  [token] {tvg_id}: {token_url[:70]}...")

    PLAYLIST.write_text("\n".join(lines), encoding="utf-8")
    print(f"Token yenilendi: {updated} kanal")


if __name__ == "__main__":
    main()
