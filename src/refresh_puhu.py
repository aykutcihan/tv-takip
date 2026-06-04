"""
Puhu TV kanallarinin yuksek cozunurluklu stream URL lerini yeniler.
Patchright ile sayfayi acar, m3u8 URL yi yakalar, playlist e yazar.
"""
from __future__ import annotations
import re
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
PLAYLIST = ROOT / "playlist.m3u"

CHANNELS = [
    {
        "name":          "NTV",
        "page":          "https://puhutv.com/ntv-canli-yayin",
        "playlist_match":"puhutv.ntv",
        "cdn_pattern":   "daioncdn.net/ntv",
        "prefer_quality":"1080p",
    },
    {
        "name":          "Star TV",
        "page":          "https://puhutv.com/star-tv-canli-yayin",
        "playlist_match":"puhutv.startv",
        "cdn_pattern":   "daioncdn.net/startv",
        "prefer_quality":"1080p",
    },
    {
        "name":          "Kral Pop TV",
        "page":          "https://puhutv.com/kral-pop-tv-canli-yayin",
        "playlist_match":"puhutv.kralpoptv",
        "cdn_pattern":   "daioncdn.net/kralpoptv",
        "prefer_quality":"1080p",
    },
    {
        "name":          "CGTN Documentary",
        "page":          "https://puhutv.com/cgtn-documentary-canli-yayin-izle",
        "playlist_match":"puhutv.cgtn",
        "cdn_pattern":   "mncdn.com/dogusdyg_drone/cgtn",
        "prefer_quality":"playlist",
    },
]


def get_stream_url(page, cdn_pattern: str, prefer_quality: str) -> str | None:
    captured = []

    def on_request(req):
        if cdn_pattern in req.url and "m3u8" in req.url:
            captured.append(req.url)

    page.on("request", on_request)
    try:
        page.wait_for_timeout(6000)
    finally:
        page.remove_listener("request", on_request)

    if not captured:
        return None

    # Tercih edilen kaliteyi sec
    preferred = [u for u in captured if prefer_quality in u]
    if preferred:
        return preferred[0]

    # En yuksek kaliteyi sec
    for q in ["1080p", "720p", "480p", "360p"]:
        qs = [u for u in captured if q in u]
        if qs:
            return qs[0]

    return captured[0]


def update_playlist(playlist_match: str, new_url: str) -> int:
    lines = PLAYLIST.read_text(encoding="utf-8").splitlines()
    updated = 0
    for i, line in enumerate(lines):
        if playlist_match in line and line.startswith("https"):
            if lines[i] != new_url:
                lines[i] = new_url
                updated += 1
    if updated:
        PLAYLIST.write_text("\n".join(lines), encoding="utf-8")
    return updated


def main():
    print("Puhu TV stream URL leri yenileniyor...")
    from patchright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        for ch in CHANNELS:
            print(f"\n  {ch['name']} -> {ch['page']}")
            page = ctx.new_page()
            try:
                page.goto(ch["page"], wait_until="networkidle", timeout=25000)
                new_url = get_stream_url(page, ch["cdn_pattern"], ch["prefer_quality"])
                if new_url:
                    n = update_playlist(ch["playlist_match"], new_url)
                    print(f"  OK: {n} URL guncellendi -> {new_url[:80]}...")
                else:
                    print(f"  !! URL alinamadi")
            except Exception as e:
                print(f"  !! Hata: {e}")
            finally:
                page.close()

        ctx.close()
        browser.close()

    print("\nTamamlandi.")


if __name__ == "__main__":
    main()
