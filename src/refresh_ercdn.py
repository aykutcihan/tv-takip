"""
ercdn.net, mncdn.com ve duhnet.tv gibi token-bazli stream URL'lerini yeniler.
Her kanal icin kendi resmi sitesini Playwright ile acar, yeni token'li URL'i yakalar.
Mevcut kaynaklar degistirilmez — sadece token guncellenir.
"""
from __future__ import annotations
import re
import sys
import io
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
PLAYLIST = ROOT / "playlist.m3u"

# CDN pattern -> (kanal_adi, kaynak_url, beklenen_url_parcasi)
CHANNELS = [
    {
        "name": "ATV Avrupa",
        "source_page": "https://www.atvavrupa.tv/canli-yayin",
        "cdn_pattern": "ercdn.net/atvavrupa",
        "playlist_match": "atvavrupa",
    },
    {
        "name": "A Para",
        "source_page": "https://www.apara.com.tr/canli",
        "cdn_pattern": "ercdn.net/aparahd",
        "playlist_match": "aparahd",
    },
    {
        "name": "A Spor",
        "source_page": "https://www.aspor.com.tr/canli-yayin",
        "cdn_pattern": "ercdn.net/asporhd",
        "playlist_match": "asporhd",
    },
    {
        "name": "EuroStar",
        "source_page": "https://www.eurostar.com.tr/canli-izle",
        "cdn_pattern": "mncdn.com/dogusdyg_eurostar",
        "playlist_match": "dogusdyg_eurostar",
    },
    {
        "name": "CNN Turk (duhnet)",
        "source_page": "https://www.cnnturk.com/canli-yayin",
        "cdn_pattern": "duhnet.tv",
        "playlist_match": "duhnet.tv",
    },
]


def get_fresh_url(page, source_page: str, cdn_pattern: str) -> str | None:
    captured = []

    def on_request(req):
        if cdn_pattern in req.url and "m3u8" in req.url:
            captured.append(req.url)

    page.on("request", on_request)
    try:
        page.goto(source_page, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(5000)
        # play butonuna tikla
        for sel in ["button[class*=play]", ".play-button", "video", "[class*=player]"]:
            try:
                page.click(sel, timeout=2000)
                page.wait_for_timeout(3000)
                break
            except:
                pass
    except Exception as e:
        print(f"    Sayfa hatasi: {e}")
    finally:
        page.remove_listener("request", on_request)

    return captured[0] if captured else None


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
    print("ercdn/mncdn/duhnet stream URL'leri yenileniyor...")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = ctx.new_page()

        for ch in CHANNELS:
            print(f"\n  {ch['name']} -> {ch['source_page']}")
            new_url = get_fresh_url(page, ch["source_page"], ch["cdn_pattern"])
            if new_url:
                n = update_playlist(ch["playlist_match"], new_url)
                print(f"  OK: {n} URL guncellendi -> {new_url[:70]}...")
            else:
                print(f"  !! URL alinamadi")

        browser.close()

    print("\nTamamlandi.")


if __name__ == "__main__":
    main()
