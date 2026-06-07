"""
streams.uzunmuhalefet.com uzerinden Turk kanallarinin stream URL'lerini yeniler.
Proxy redirect'ini takip edip arkasindaki gercek CDN URL'sini (kavuntv/ercdn/daioncdn) alir.
Bot tespiti yok — sadece HTTP GET. Playwright gerektirmez.
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

# uzunmuhalefet kanal adi -> bizim tvg-id
CHANNEL_MAP = {
    "NOW TV":           "tr.now",
    "Show TV":          "tr.showtv",
    "TV8":              "tr.tv8",
    "TV 8":             "tr.tv8",
    "TV 8.5":           "tr.tv85",
    "ATV":              "tr.atv",
    "Star TV":          "tr.startv",
    "Kanal D":          "tr.kanald",
    "Kanal 7":          "tr.kanal7",
    "TYT Türk":         "tr.tytturk",
    "Show Türk":        "tr.showturk",
    "Kanal 7 Avrupa":   "tr.kanal7avrupa",
    "ATV Avrupa":       "tr.atvavrupa",
    "Euro D":           "tr.eurod",
    "A Haber":          "tr.ahaber",
    "Ulusal Kanal":     "tr.ulusalkanal",
    "Bloomberg HT":     "tr.bloomberght",
    "CNBC-e":           "tr.cnbce",
    "Habertürk":        "tr.haberturk",
    "TRT Spor":         "tr.trtspor",
    "TRT Spor Yıldız":  "tr.trtsporyildiz",
    "A Spor":           "tr.aspor",
    "HT Spor":          "tr.htspor",
    "Ekol Sports":      "tr.ekolsports",
    "Tivibu Spor":      "tr.tivibuspor",
    "TRT 2":            "tr.trt2",
    "TLC":              "tr.tlc",
    "DMAX":             "tr.dmax",
    "D Max":            "tr.dmax",
    "TRT Belgesel":     "tr.trtbelgesel",
    "Dream Türk":       "tr.dreamturk",
    "Kanal B":          "tr.kanalb",
    "TV 100":           "tr.tv100",
    "TGRT Haber":       "tr.tgrthaber",
    "Ekol TV":          "tr.ekoltvhaber",
    "Tele On":          "tr.teleon",
    "TV Net":           "tr.tvnet",
    "TVNET":            "tr.tvnet",
}

REPLACE_SRCS = re.compile(r'tvkulesi|kavuntv\.net|uzunmuhalefet\.com')


def fetch_proxy_map():
    """uzunmuhalefet playlist -> {tvg-id: proxy_url}"""
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
            tvg = CHANNEL_MAP.get(name)
            if tvg and url:
                result[tvg] = url
        i += 1
    print(f"  {len(result)} kanal eslesti.")
    return result


def resolve_url(proxy_url):
    """
    Proxy URL'nin redirect hedefini al — kavuntv'ye HICBIR ISTEK ATMAZ.
    Sadece uzunmuhalefet.com'un 302 Location header'ini okur.
    """
    try:
        r = requests.get(proxy_url, timeout=15, headers=HEADERS,
                         allow_redirects=False)  # redirect TAKIP ETME
        if r.status_code in (301, 302, 303, 307, 308):
            loc = r.headers.get('Location', '')
            if loc.startswith('http'):
                return loc  # kavuntv/ercdn URL'si — hic baglanti kurmadik
    except Exception:
        pass
    return proxy_url


def main():
    proxy_map = fetch_proxy_map()
    if not proxy_map:
        print("Esleme bos, cikiliyor.")
        return

    lines   = PLAYLIST.read_text(encoding='utf-8').splitlines()
    updated = 0

    for tvg_id, proxy_url in proxy_map.items():
        # Redirect'i takip et -> gercek CDN URL'si (kavuntv/ercdn/daioncdn)
        cdn_url = resolve_url(proxy_url)
        src = ('kavuntv'  if 'kavuntv'  in cdn_url else
               'ercdn'    if 'ercdn'    in cdn_url else
               'daioncdn' if 'daioncdn' in cdn_url else
               'uzm-proxy')
        print(f"  {tvg_id:30s} -> proxy + {src}")

        # Playlist'te bu tvg-id'li URL satirlarini guncelle:
        # - Ilk eslesen tvkulesi/kavuntv/uzunmuhalefet satirini -> proxy_url (ONCELIK)
        # - Hemen ardindan cdn_url farkli ise yaz (FALLBACK)
        for i, line in enumerate(lines):
            if not line.startswith('#EXTINF:') or f'tvg-id="{tvg_id}"' not in line:
                continue
            j = i + 1
            while j < len(lines) and lines[j].startswith('#') and not lines[j].startswith('#EXTINF'):
                j += 1
            if j >= len(lines) or not lines[j].startswith('http'):
                continue
            cur = lines[j]
            if REPLACE_SRCS.search(cur):
                # Proxy URL'yi oncelikli olarak yaz
                if cur != proxy_url:
                    lines[j] = proxy_url
                    updated += 1
                # CDN URL farkli ise bir sonraki satiri kontrol et / ekle
                if cdn_url != proxy_url:
                    k = j + 1
                    # Bos satirlari atla
                    while k < len(lines) and lines[k] == '':
                        k += 1
                    if k < len(lines) and REPLACE_SRCS.search(lines[k]):
                        # Mevcut CDN satirini guncelle
                        if lines[k] != cdn_url:
                            lines[k] = cdn_url
                            updated += 1
                    elif k >= len(lines) or lines[k].startswith('#EXTINF') or lines[k].startswith('#'):
                        # CDN satirini proxy satirinin hemen ardindan ekle
                        lines.insert(j + 1, cdn_url)
                        updated += 1

    PLAYLIST.write_text('\n'.join(lines), encoding='utf-8')
    print(f"\nTamamlandi: {updated} URL guncellendi")


if __name__ == '__main__':
    main()
