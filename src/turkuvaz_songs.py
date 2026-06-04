"""
Turkuvaz radyolarinin su an calani ceker, turkuvaz-songs.json yazar.
Playwright ile sayfayi acar, dinamik icerikten sarki bilgisini alir.
"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT   = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "turkuvaz-songs.json"

STATIONS = {
    'turkuvaz.radyoturkuvaz':    'radyoturkuvaz',
    'turkuvaz.turkuvazromantik': 'turkuvazromantik',
    'turkuvaz.turkuvazefsane':   'turkuvazefsane',
    'turkuvaz.ahaberradyo':      'ahaberradyo',
    'turkuvaz.anewsradyo':       'anewsradyo',
    'turkuvaz.asporradyo':       'asporradyo',
    'turkuvaz.radyosoft':        'radyosoft',
    'turkuvaz.turkuvazanadolu':  'turkuvazanadolu',
    'turkuvaz.turkuvazmusiki':   'turkuvazmusiki',
    'turkuvaz.turkuvaznostalji': 'turkuvaznostalji',
    'turkuvaz.aparaRadyo':       'aparaRadyo',
}


def fetch_song(page, slug: str) -> dict | None:
    try:
        page.goto(
            f'https://www.turkuvazradyolar.com/{slug}',
            wait_until='domcontentloaded',
            timeout=15000,
        )
        page.wait_for_timeout(3000)

        title  = page.eval_on_selector('#playingTitle',  'el => el.innerText.trim()') or ''
        singer = page.eval_on_selector('#singer',        'el => el.innerText.trim()') or ''

        if title or singer:
            return {'title': title, 'artist': singer, 'cover': ''}
        return None
    except Exception as e:
        print(f'  [hata] {slug}: {e}')
        return None


def main():
    result = {}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = ctx.new_page()

        for tvg_id, slug in STATIONS.items():
            info = fetch_song(page, slug)
            if info:
                result[tvg_id] = info
                print(f'  OK {tvg_id}: {info.get("artist","")} - {info.get("title","")}')
            else:
                print(f'  -- {tvg_id}: veri yok')

        ctx.close()
        browser.close()

    OUTPUT.write_text(
        json.dumps(result, ensure_ascii=False, separators=(',', ':')),
        encoding='utf-8',
    )
    print(f'\nturkuvaz-songs.json yazildi: {len(result)} kanal')


if __name__ == '__main__':
    main()
