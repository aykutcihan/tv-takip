"""
kavuntv.net kaynakli kanallarin stream URL'lerini yeniler.
Bot tespitinden kacmak icin patchright + gercek browser davranisi kullanir.
"""
import sys, io, re, json, warnings, random, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
warnings.filterwarnings('ignore')

from patchright.sync_api import sync_playwright
from pathlib import Path

ROOT      = Path(__file__).resolve().parent.parent
PLAYLIST  = ROOT / "playlist.m3u"
SLUGS_FILE = ROOT / "channel_slugs.json"

KAVU_BASE = "https://amp.kavuntv.net"

# Gercek browser gibi gorunen user-agent'lar
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
]


def fetch_stream(ctx, url):
    streams = []
    page = ctx.new_page()

    def on_req(r):
        u = r.url.lower()
        if '.m3u8' in u and 'chunk' not in u and 'manifest' not in u:
            streams.append(r.url)

    try:
        page.on('request', on_req)
        # networkidle: tum istekler bitene kadar bekle
        page.goto(url, wait_until='networkidle', timeout=25000)
        # Ek bekleme - player yuklenmesi icin
        page.wait_for_timeout(3000)

        # Hala bulunamadiysa play/video elementine tikla
        if not streams:
            for sel in ['.video-js', 'video', '.plyr', '.jwplayer', '[class*=player]', 'button']:
                try:
                    page.click(sel, timeout=1500)
                    page.wait_for_timeout(2000)
                    if streams:
                        break
                except Exception:
                    pass

    except Exception:
        pass
    finally:
        try:
            page.remove_listener('request', on_req)
        except Exception:
            pass
        try:
            page.close()
        except Exception:
            pass

    return list(dict.fromkeys(streams))


def main():
    slug_map = json.loads(SLUGS_FILE.read_text(encoding='utf-8'))

    lines = PLAYLIST.read_text(encoding='utf-8').splitlines()
    updated = 0
    failed  = 0

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--window-size=1920,1080',
            ]
        )
        ctx = browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={'width': 1920, 'height': 1080},
            locale='tr-TR',
            timezone_id='Europe/Istanbul',
            extra_http_headers={
                'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
        )
        # webdriver izini gizle
        ctx.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            Object.defineProperty(navigator, 'languages', {get: () => ['tr-TR', 'tr', 'en-US']});
            window.chrome = { runtime: {} };
        """)

        # Once ana sayfaya git - cookie ve session olustur
        try:
            warmup = ctx.new_page()
            warmup.goto(KAVU_BASE, wait_until='domcontentloaded', timeout=15000)
            warmup.wait_for_timeout(2000)
            warmup.close()
        except Exception:
            pass

        for display_name, slug in slug_map.items():
            streams = fetch_stream(ctx, f"{KAVU_BASE}/{slug}")

            if not streams:
                print(f"  !! {display_name} ({slug}) alinamadi")
                failed += 1
                # Kisa bekleme - rate limit'e takilmamak icin
                time.sleep(0.5)
                continue

            new_url = streams[0]

            # Playlist guncelle
            name_clean = re.sub(r'[^a-z0-9]', '', display_name.lower())
            for i, line in enumerate(lines):
                if not line.startswith('#EXTINF:'):
                    continue
                line_name_m = re.search(r',(.+)$', line)
                if not line_name_m:
                    continue
                line_name     = line_name_m.group(1).strip()
                line_name_bare = re.sub(r'\s*\((tvku|kavu|v-tvku|v-kavu)\)\s*', '', line_name).strip()
                line_clean    = re.sub(r'[^a-z0-9]', '', line_name_bare.lower())

                if line_clean == name_clean:
                    j = i + 1
                    while j < len(lines) and lines[j].startswith('#') and not lines[j].startswith('#EXTINF'):
                        j += 1
                    if j < len(lines) and lines[j].startswith('http'):
                        cur_url = lines[j]
                        if 'kavuntv.net' in cur_url or 'tvkulesi' in cur_url or slug in cur_url:
                            if cur_url != new_url:
                                lines[j] = new_url
                                updated += 1

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
