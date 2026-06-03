"""
destanfilm.com/film/en-son-cikan-filmler/ sayfasini tarar.
Yeni film varsa ekler, mevcut filmlerin URL'lerini yeniler.
films.m3u dosyasina yazar.
"""
import sys, io, re, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILMS_M3U = ROOT / "films.m3u"
FILMS_DB  = ROOT / "cache" / "films_db.json"
SOURCE_URL = "https://www.destanfilm.com/film/en-son-cikan-filmler/"

HEADER = "#EXTM3U\n"


def load_db():
    if FILMS_DB.exists():
        return json.loads(FILMS_DB.read_text(encoding='utf-8'))
    return {}


def save_db(db):
    FILMS_DB.parent.mkdir(exist_ok=True)
    FILMS_DB.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding='utf-8')


def get_film_list(page):
    page.goto(SOURCE_URL, wait_until='domcontentloaded', timeout=20000)
    page.wait_for_timeout(2000)
    soup = BeautifulSoup(page.content(), 'lxml')
    films = []
    for article in soup.find_all('article'):
        a = article.find('a', href=True)
        img = article.find('img')
        title_el = article.find(['h2', 'h3', 'h4'])
        if not a:
            continue
        title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
        title = re.sub(r'\s*izle\s*$', '', title, flags=re.I).strip()
        poster = ''
        if img:
            poster = img.get('data-src') or img.get('src') or ''
        films.append({'title': title, 'url': a['href'], 'poster': poster})
    return films


def get_embed_info(page, film_url):
    """Film sayfasindan embed tipini ve URL'ini dondurur: ('vidmoly'|'youtube'|None, url)"""
    try:
        page.goto(film_url, wait_until='domcontentloaded', timeout=20000)
        page.wait_for_timeout(2000)
        content = page.content()

        idx = content.find('video_url')
        if idx < 0:
            return None, None
        chunk = content[idx:idx+600]

        # vidmoly
        m = re.search(r'vidmoly\.net[\\/]+(embed-[^"\\]+)', chunk)
        if m:
            slug = m.group(1).replace('\\/', '/').replace('\\', '')
            return 'vidmoly', f'https://vidmoly.net/{slug}'

        # youtube
        m = re.search(r'youtube\.com[\\/]+embed[\\/]+([A-Za-z0-9_-]{8,12})', chunk)
        if m:
            return 'youtube', f'https://www.youtube.com/watch?v={m.group(1)}'

        return None, None
    except Exception as e:
        print(f"    embed hatasi: {e}")
        return None, None


def get_stream_from_vidmoly(page, embed_url):
    streams = []
    def on_req(r):
        if '.m3u8' in r.url and 'chunk' not in r.url:
            streams.append(r.url)
    try:
        page.on('request', on_req)
        page.goto(embed_url, wait_until='domcontentloaded', timeout=15000)
        page.wait_for_timeout(3500)
        page.remove_listener('request', on_req)
    except Exception:
        try:
            page.remove_listener('request', on_req)
        except Exception:
            pass
    masters = [u for u in streams if 'master' in u]
    return masters[0] if masters else (streams[0] if streams else None)


def get_stream_from_youtube(video_url):
    import subprocess
    try:
        result = subprocess.run(
            ['yt-dlp', '--get-url', '-f', 'b', '--no-warnings', video_url],
            capture_output=True, text=True, timeout=30
        )
        url = result.stdout.strip().split('\n')[0]
        return url if url and 'http' in url else None
    except Exception as e:
        print(f"    yt-dlp hatasi: {e}")
        return None


def write_m3u(db):
    lines = [HEADER]
    for slug, info in db.items():
        if not info.get('stream'):
            continue
        title  = info.get('title', slug)
        poster = info.get('poster', '')
        stream = info['stream']
        lines.append(f'#EXTINF:-1 tvg-logo="{poster}" group-title="Film",{title}')
        lines.append(stream)
    FILMS_M3U.write_text('\n'.join(lines), encoding='utf-8')
    print(f"films.m3u yazildi: {len(lines)//2} film")


def main():
    db = load_db()
    print(f"Mevcut veritabani: {len(db)} film")

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

        # Film listesini al
        print(f"\nKaynak taranıyor: {SOURCE_URL}")
        films = get_film_list(page)
        print(f"{len(films)} film bulundu")

        new_count = 0
        updated_count = 0

        for film in films:
            slug = film['url'].rstrip('/').split('/')[-1]

            # Yeni film mi?
            is_new = slug not in db
            if is_new:
                db[slug] = {
                    'title':  film['title'],
                    'url':    film['url'],
                    'poster': film['poster'],
                    'stream': None,
                }

            # Embed tipini ve URL'ini al
            embed_type, embed_url = get_embed_info(page, film['url'])
            if not embed_url:
                print(f"  ?? {film['title']} - embed bulunamadi")
                continue

            # Stream URL al
            if embed_type == 'vidmoly':
                stream = get_stream_from_vidmoly(page, embed_url)
            elif embed_type == 'youtube':
                stream = get_stream_from_youtube(embed_url)
                print(f"     [youtube] {film['title']}")
            else:
                stream = None

            if not stream:
                print(f"  !! {film['title']} - stream alinamadi ({embed_type})")
                continue

            db[slug]['stream'] = stream
            db[slug]['poster'] = film['poster'] or db[slug].get('poster', '')

            if is_new:
                new_count += 1
                print(f"  +  {film['title']}")
            else:
                updated_count += 1
                print(f"  ~  {film['title']}")

        ctx.close()
        browser.close()

    save_db(db)
    write_m3u(db)
    print(f"\nTamamlandi: {new_count} yeni, {updated_count} guncellendi")


if __name__ == '__main__':
    main()
