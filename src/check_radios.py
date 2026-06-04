"""
radios_playlist.m3u'daki radyo stream URL'lerini kontrol eder.
Cevap vermeyen URL'leri rapor eder.
"""
import sys, io, re, requests, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAYLIST = ROOT / "radios_playlist.m3u"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}


def check_url(url: str, timeout: int = 8) -> tuple[bool, int]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, stream=True)
        return r.status_code < 400, r.status_code
    except Exception:
        return False, 0


def main():
    lines = PLAYLIST.read_text(encoding='utf-8').splitlines()

    urls = {}  # url -> kanal adı
    current_name = ''
    for line in lines:
        if line.startswith('#EXTINF:'):
            m = re.search(r',(.+)$', line)
            current_name = m.group(1).strip() if m else '?'
        elif line.startswith('http') and current_name:
            urls[line] = current_name
            current_name = ''

    print(f"Toplam {len(urls)} radyo stream kontrol ediliyor...\n")

    ok_count = 0
    fail_count = 0

    for url, name in urls.items():
        ok, status = check_url(url)
        if ok:
            ok_count += 1
        else:
            fail_count += 1
            print(f"HATA [{status}]: {name}")
            print(f"  URL: {url}")
        time.sleep(0.2)

    print(f"\nSonuç: {ok_count} OK, {fail_count} HATA")
    if fail_count > 0:
        print("\nNot: Hatalı stream'ler için manuel güncelleme gerekebilir.")


if __name__ == '__main__':
    main()
