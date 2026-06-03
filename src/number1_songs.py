"""
Number1 radyolarinin su an calani ceker, number1-songs.json yazar.
xspf API'si olan istasyonlar icin dogrudan API kullanir,
diger istasyonlar icin Playwright ile sayfa #metadata okur.
"""
import sys, io, re, json, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT   = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "number1-songs.json"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
           'Referer': 'https://www.numberone.com.tr/'}

# tvg-id -> (page_url, xspf_url or None)
STATIONS = {
    'number1.fm':          ('https://www.numberone.com.tr/2015/12/17/number1-fm-dinle-canli-radyo-dinle/', None),
    'number1.slow':        ('https://www.numberone.com.tr/2015/12/16/number1-slow-canli-radyo-dinle/', None),
    'number1.dance':       ('https://www.numberone.com.tr/2015/12/17/number1-dance-canli-radyo-dinle/', None),
    'number1.heart':       ('https://www.numberone.com.tr/2015/12/17/number1-heart-canli-radyo-dinle/', None),
    'number1.lounge':      ('https://www.numberone.com.tr/2016/03/08/number1-lounge-canli-radyo-dinle/', None),
    'number1.deephouse':   ('https://www.numberone.com.tr/2016/04/15/number1-deep-house-canli-radyo-dinle/', None),
    'number1.disco':       ('https://www.numberone.com.tr/2017/02/09/number1-disco-canli-radyo-dinle/', None),
    'number1.greek':       ('https://www.numberone.com.tr/2016/09/29/number1-greek-dinle-canli-radyo-dinle/', None),
    'number1.rock':        ('https://www.numberone.com.tr/2016/01/13/number1-rock-canli-radyo-dinle/', None),
    'number1.bestof':      ('https://www.numberone.com.tr/2017/08/16/best-of-number1-canli-radyo-dinle/', None),
    'number1.turkrap':     ('https://www.numberone.com.tr/2018/10/25/number1-turk-rap-canli-radyo-dinle/', None),
    'number1.ask':         ('https://www.numberone.com.tr/2026/04/22/nr1-ask/', None),
    'number1.petrol':      ('https://www.numberone.com.tr/2021/09/23/nr1-po-radyo-canli-radyo-dinle/', None),
    'number1.turkdamar':   ('https://www.numberone.com.tr/2017/07/10/nr1-turk-damar-radyo-dinle/', 'https://n10101m.mediatriple.net/trdamar.xspf'),
    'number1.turkslow':    ('https://www.numberone.com.tr/2015/12/20/nr1-turk-slow-canli-radyo-dinle/', 'https://n10101m.mediatriple.net/numberoneturkslow.xspf'),
    'number1.turk90lar':   ('https://www.numberone.com.tr/2017/02/08/number1-90lar-canli-radyo-dinle/', 'https://n10101m.mediatriple.net/numberone90s.xspf'),
    'number1.ellerhavaya': ('https://www.numberone.com.tr/2016/09/29/number1-eller-havaya-canli-radyo-dinle/', 'https://n10101m.mediatriple.net/ellerhavaya.xspf'),
}


def get_from_xspf(xspf_url: str) -> str | None:
    try:
        r = requests.get(xspf_url, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            m = re.search(r'<title>([^<]+)</title>', r.text)
            if m:
                return m.group(1).strip()
    except Exception:
        pass
    return None


def main():
    result = {}

    # xspf'i olan istasyonlar
    for tvg_id, (_, xspf_url) in STATIONS.items():
        if xspf_url:
            song = get_from_xspf(xspf_url)
            if song:
                result[tvg_id] = {'title': song, 'artist': '', 'cover': ''}
                print(f'xspf {tvg_id}: {song}')

    # Sayfa scraping gereken istasyonlar
    page_stations = {k: v for k, v in STATIONS.items() if v[1] is None}
    print(f'\nPlaywright ile {len(page_stations)} istasyon taranıyor...')

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=['--no-sandbox'])
        ctx = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36')
        page = ctx.new_page()

        for tvg_id, (page_url, _) in page_stations.items():
            try:
                page.goto(page_url, wait_until='domcontentloaded', timeout=15000)
                page.wait_for_timeout(2000)
                metadata = page.evaluate('() => { const el = document.getElementById("metadata"); return el ? el.innerText.trim() : ""; }')
                if metadata and metadata != 'undefined':
                    result[tvg_id] = {'title': metadata, 'artist': '', 'cover': ''}
                    print(f'page {tvg_id}: {metadata[:60]}')
                else:
                    print(f'!!   {tvg_id}: bos')
            except Exception as e:
                print(f'!!   {tvg_id}: {e}')

        ctx.close()
        browser.close()

    OUTPUT.write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
    print(f'\nnumber1-songs.json yazildi: {len(result)} istasyon')


if __name__ == '__main__':
    main()
