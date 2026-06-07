"""
inat_discover.py — inattvgiris.pro üzerinden güncel domain ve CDN URL'ini bulur.
Sonucu config/inat_config.json'a yazar. Proxy bu dosyayı okur.

Calistir: python3 src/inat_discover.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "inat_config.json"

GATEWAY = "https://inattvgiris.pro/inat-tv34/"
TEST_CHANNEL = "trt1"


def discover():
    from patchright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        cdn_url = None
        def on_request(req):
            nonlocal cdn_url
            if "mono.m3u8" in req.url and cdn_url is None:
                cdn_url = req.url
        page.on("request", on_request)

        # 1. Gateway'e git
        print(f"Gateway aciliyor: {GATEWAY}")
        page.goto(GATEWAY, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)

        # 2. Sayfadaki ilk kanal/stream linkine tikla
        links = page.eval_on_selector_all(
            'a[href*="channel.html"], a[href*="canli"], a[href*="live"], a[href*="id="]',
            'els => els.map(e => e.href)'
        )
        print(f"Bulunan linkler: {links[:5]}")

        domain = None
        for link in links[:5]:
            if not link or link == page.url:
                continue
            print(f"Link deneniyor: {link}")
            page.goto(link, wait_until="networkidle", timeout=20000)
            page.wait_for_timeout(5000)
            current_url = page.url
            m = re.match(r"(https?://[^/]+)", current_url)
            if m:
                domain = m.group(1)
                print(f"Domain bulundu: {domain}")
                if cdn_url:
                    break

        # 3. Hâlâ CDN yoksa doğrudan test kanalını dene
        if not cdn_url and domain:
            channel_page = f"{domain}/channel.html?id={TEST_CHANNEL}"
            print(f"Direkt kanal: {channel_page}")
            page.goto(channel_page, wait_until="networkidle", timeout=20000)
            page.wait_for_timeout(6000)

        if not cdn_url:
            # Son çare: mevcut domain üzerinde dene
            domain = domain or "https://inattv1311.xyz"
            channel_page = f"{domain}/channel.html?id={TEST_CHANNEL}"
            print(f"Son deneme: {channel_page}")
            page.goto(channel_page, wait_until="networkidle", timeout=20000)
            page.wait_for_timeout(6000)

        browser.close()

    if not cdn_url:
        print("CDN URL bulunamadi!")
        return False

    # CDN base URL'i çıkar (kanal ID'sini at)
    cdn_base = re.sub(rf"/{TEST_CHANNEL}/.*", "", cdn_url)
    print(f"CDN base: {cdn_base}")

    config = {
        "domain": domain,
        "referer": domain + "/",
        "origin": domain,
        "cdn_base": cdn_base,
    }

    CONFIG_PATH.parent.mkdir(exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Config yazildi: {CONFIG_PATH}")
    print(json.dumps(config, indent=2, ensure_ascii=False))
    return True


if __name__ == "__main__":
    ok = discover()
    sys.exit(0 if ok else 1)
