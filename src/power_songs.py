"""
PowerApp radyolarinin su an calan sarki bilgisini ceker.
power-songs.json dosyasina yazar.
Format: { "powerapp.powerturk": { "title": "...", "artist": "...", "cover": "..." } }
"""
import sys, io, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT   = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "power-songs.json"

SLUGS = [
    'powerfm', 'powerturk', 'powerplus', 'powerpop', 'powerlove',
    'powersmooth', 'powerextralounge', 'powerearth', 'powerdeep',
    'powerturkslow', 'powerturkrap', 'powerturkakustik',
    'powerturktaptaze', 'powerturkdans', 'powerdance',
    'powergreece', 'powerrbhiphop', 'powersalsa', 'powergold',
    'powersmoothjazz',
]


def fetch_channel(page, slug: str) -> dict | None:
    data_store = {}

    def capture(r):
        if 'v3/Route/get' in r.url and slug in r.url:
            try:
                data_store['body'] = r.body()
            except Exception:
                pass

    page.on('response', capture)
    try:
        page.goto(
            f'https://www.powerapp.com.tr/{slug}/song-history/',
            wait_until='networkidle',
            timeout=20000,
        )
        page.wait_for_timeout(2000)
    except Exception as e:
        print(f'  [hata] {slug}: {e}')
    finally:
        page.remove_listener('response', capture)

    if 'body' not in data_store:
        return None

    try:
        d = json.loads(data_store['body']).get('data', {})
    except Exception:
        return None

    ch_id  = d.get('ID')
    img    = d.get('image', {})
    logo   = img.get('prefix', '') + '150x150' + img.get('suffix', '') if img else ''

    timeline = d.get('timeline', [])
    if not timeline:
        return {'logo': logo} if logo else None

    current  = timeline[0]
    raw      = current.get('artistTitle', '')
    # "Sanatçı - Şarkı" veya sadece başlık olabilir
    if ' - ' in raw:
        parts  = raw.split(' - ', 1)
        artist = parts[0].strip()
        title  = parts[1].strip()
    else:
        artist = ''
        title  = raw.strip()

    # Kapak resmi — artwork URL'si varsa al
    artwork = current.get('artwork', {}) or {}
    if isinstance(artwork, dict):
        prefix = artwork.get('prefix', '')
        suffix = artwork.get('suffix', '')
        cover  = prefix + '300x300' + suffix if prefix else ''
    else:
        cover = ''

    return {
        'title':  title,
        'artist': artist,
        'cover':  cover or logo,
        'logo':   logo,
        'remaining': current.get('remainingSeconds', 0),
        'duration':  current.get('duration', 0),
    }


def main():
    result = {}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for slug in SLUGS:
            ctx  = browser.new_context()
            page = ctx.new_page()
            info = fetch_channel(page, slug)
            ctx.close()

            key = f'powerapp.{slug}'
            if info:
                result[key] = info
                song = f'{info.get("artist","")} - {info.get("title","")}' if info.get('artist') else info.get('title', '')
                print(f'  OK {key}: {song[:50]}')
            else:
                print(f'  !! {key}: veri alinamadi')

        browser.close()

    OUTPUT.write_text(
        json.dumps(result, ensure_ascii=False, separators=(',', ':')),
        encoding='utf-8',
    )
    print(f'\npower-songs.json yazildi: {len(result)} kanal')


if __name__ == '__main__':
    main()
