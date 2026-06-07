"""
streams.uzunmuhalefet.com uzerinden Turk kanallarinin stream URL'lerini yeniler.
Playlist'teki TUM kanallarla otomatik eslestirme yapar — elle liste tutmaya gerek yok.
Bot tespiti yok, Playwright gerektirmez.
"""
import sys, io, re, requests, warnings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
warnings.filterwarnings('ignore')
from pathlib import Path

ROOT     = Path(__file__).resolve().parent.parent
PLAYLIST = ROOT / "playlist.m3u"

SOURCE_M3U = "https://streams.uzunmuhalefet.com/lists/tr.m3u"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'tr-TR,tr;q=0.9',
    'Referer': 'https://streams.uzunmuhalefet.com/',
}

# Bu kaynaklardaki URL'leri uzunmuhalefet ile guncelle
REPLACE_SRCS = re.compile(r'tvkulesi|kavuntv\.net|uzunmuhalefet\.com')

def normalize(s):
    """Kanal ismi eslesme icin normalize et."""
    s = s.lower()
    s = re.sub(r'[^a-z0-9]', '', s)
    # Yaygin kisaltmalar
    s = s.replace('türk', 'turk').replace('ü','u').replace('ı','i')
    s = s.replace('ö','o').replace('ş','s').replace('ç','c').replace('ğ','g')
    return s


def fetch_source_playlist():
    """uzunmuhalefet playlist -> {normalize(name): proxy_url}"""
    print(f"Kaynak indiriliyor: {SOURCE_M3U}")
    try:
        r = requests.get(SOURCE_M3U, timeout=30, headers=HEADERS)
        r.raise_for_status()
    except Exception as e:
        print(f"  !! {e}")
        return {}

    result, i = {}, 0
    lines = r.text.splitlines()
    while i < len(lines):
        if lines[i].startswith('#EXTINF'):
            m = re.search(r',(.+)$', lines[i])
            name = m.group(1).strip() if m else ''
            j = i + 1
            while j < len(lines) and lines[j].startswith('#'):
                j += 1
            url = lines[j] if j < len(lines) and lines[j].startswith('http') else ''
            if name and url:
                result[normalize(name)] = (name, url)
        i += 1

    print(f"  Kaynak: {len(result)} kanal.")
    return result


def build_our_channels(lines):
    """Kendi playlist'imizdeki {normalize(name): [idx]} haritasi."""
    our = {}
    for i, line in enumerate(lines):
        if not line.startswith('#EXTINF:'):
            continue
        m = re.search(r',(.+)$', line)
        if not m:
            continue
        name = m.group(1).strip()
        key  = normalize(name)
        our.setdefault(key, []).append(i)
    return our


def main():
    source = fetch_source_playlist()
    if not source:
        print("Kaynak bos.")
        return

    lines    = PLAYLIST.read_text(encoding='utf-8').splitlines()
    our_map  = build_our_channels(lines)
    updated  = 0
    matched  = 0

    for norm_key, (src_name, proxy_url) in source.items():
        # Bizim playlist'te bu kanal var mi?
        extinf_indices = our_map.get(norm_key, [])
        if not extinf_indices:
            continue

        matched += 1
        for i in extinf_indices:
            # URL satirini bul
            j = i + 1
            while j < len(lines) and lines[j].startswith('#') and not lines[j].startswith('#EXTINF'):
                j += 1
            if j >= len(lines) or not lines[j].startswith('http'):
                continue
            cur = lines[j]
            # Sadece tvkulesi/kavuntv/uzunmuhalefet URL'lerini guncelle
            if REPLACE_SRCS.search(cur) and cur != proxy_url:
                lines[j] = proxy_url
                updated += 1

        print(f"  ok  {src_name}")

    PLAYLIST.write_text('\n'.join(lines), encoding='utf-8')
    print(f"\nTamamlandi: {matched} kanal eslesti, {updated} URL guncellendi")


if __name__ == '__main__':
    main()
