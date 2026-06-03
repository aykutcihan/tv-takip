"""
tvku/kavu kaynakli kanallarin stream URL'lerini gunluk yeniler.
tvkulesi.com primary, kavuntv.net fallback.
"""
import sys, io, re, json, warnings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
warnings.filterwarnings('ignore')

from playwright.sync_api import sync_playwright
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAYLIST = ROOT / "playlist.m3u"
SLUGS_FILE = ROOT / "channel_slugs.json"

TVKU_BASE = "https://tr.tvkulesi.com"
KAVU_BASE = "https://amp.kavuntv.net"


def fetch_stream(page, url):
    streams = []

    def on_req(r):
        if '.m3u8' in r.url.lower() and 'chunk' not in r.url.lower():
            streams.append(r.url)

    try:
        page.on('request', on_req)
        page.goto(url, wait_until='domcontentloaded', timeout=15000)
        page.wait_for_timeout(2500)
        page.remove_listener('request', on_req)
    except Exception:
        try:
            page.remove_listener('request', on_req)
        except Exception:
            pass

    return list(dict.fromkeys(streams))


def main():
    slug_map = json.loads(SLUGS_FILE.read_text(encoding='utf-8'))
    # slug -> display_name tersten map
    slug_to_name = {v: k for k, v in slug_map.items()}

    lines = PLAYLIST.read_text(encoding='utf-8').splitlines()
    updated = 0
    failed = 0

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
        )
        ctx = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36'
        )
        ctx.add_init_script('Object.defineProperty(navigator,"webdriver",{get:()=>undefined})')
        page = ctx.new_page()

        for display_name, slug in slug_map.items():
            # Once tvkulesi, alamazsa kavuntv
            streams = fetch_stream(page, f"{TVKU_BASE}/{slug}")
            if not streams:
                streams = fetch_stream(page, f"{KAVU_BASE}/{slug}")

            if not streams:
                print(f"  !! {display_name} ({slug}) alinamadi")
                failed += 1
                continue

            new_url = streams[0]

            # Playlist'te bu slug'a ait tum satirlari guncelle
            name_clean = re.sub(r'[^a-z0-9]', '', display_name.lower())
            for i, line in enumerate(lines):
                if not line.startswith('#EXTINF:'):
                    continue
                line_name_m = re.search(r',(.+)$', line)
                if not line_name_m:
                    continue
                line_name = line_name_m.group(1).strip()
                line_name_bare = re.sub(r'\s*\((tvku|kavu|v-tvku|v-kavu)\)\s*', '', line_name).strip()
                line_clean = re.sub(r'[^a-z0-9]', '', line_name_bare.lower())

                if line_clean == name_clean:
                    # # source: satirini atla, URL satirini bul
                    j = i + 1
                    while j < len(lines) and lines[j].startswith('#') and not lines[j].startswith('#EXTINF'):
                        j += 1
                    if j < len(lines) and lines[j].startswith('http'):
                        cur_url = lines[j]
                        if 'kavuntv.net' in cur_url or 'tvkulesi' in cur_url or slug in cur_url:
                            if cur_url != new_url:
                                lines[j] = new_url
                                updated += 1

            # tvg-id = tvku.slug veya kavu.slug olan satirlari da guncelle
            for i, line in enumerate(lines):
                if f'tvg-id="tvku.{slug}"' in line or f'tvg-id="kavu.{slug}"' in line:
                    j = i + 1
                    while j < len(lines) and lines[j].startswith('#') and not lines[j].startswith('#EXTINF'):
                        j += 1
                    if j < len(lines) and lines[j].startswith('http') and lines[j] != new_url:
                        lines[j] = new_url
                        updated += 1

            print(f"  ok  {display_name}")

        ctx.close()
        browser.close()

    PLAYLIST.write_text('\n'.join(lines), encoding='utf-8')
    print(f"\nTamamlandi: {updated} URL guncellendi, {failed} alinamadi")


if __name__ == '__main__':
    main()
