"""
streams.uzunmuhalefet.com uzerinden Turk kanallarinin stream URL'lerini yeniler.
Bot tespiti yok, Playwright gerektirmez — basit HTTP istegi yeterli.
Kaynak: DonanımHaber forum / uzunmuhalefet.com (her sabah 09:30'da guncelleniyor)
"""
import sys, io, re, json, warnings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
warnings.filterwarnings('ignore')

import requests
from pathlib import Path

ROOT       = Path(__file__).resolve().parent.parent
PLAYLIST   = ROOT / "playlist.m3u"
SLUGS_FILE = ROOT / "channel_slugs.json"

SOURCE_M3U = "https://streams.uzunmuhalefet.com/lists/tr.m3u"

# streams.uzunmuhalefet.com kanal adi -> bizim tvg-id eslesmesi
# Sadece tvkulesi/kavuntv kaynakli kanallari guncelliyoruz
CHANNEL_MAP = {
    # Ulusal
    "NOW TV":          "tr.now",
    "Show TV":         "tr.showtv",
    "TV8":             "tr.tv8",
    "TV 8":            "tr.tv8",
    "TV 8.5":          "tr.tv85",
    "ATV":             "tr.atv",
    "Star TV":         "tr.startv",
    "Kanal D":         "tr.kanald",
    "Kanal 7":         "tr.kanal7",
    "TYT Turk":        "tr.tytturk",
    "TYT Türk":        "tr.tytturk",
    "Show Türk":       "tr.showturk",
    "Show Turk":       "tr.showturk",
    "Kanal 7 Avrupa":  "tr.kanal7avrupa",
    "ATV Avrupa":      "tr.atvavrupa",
    "Euro D":          "tr.eurod",
    # Haber
    "A Haber":         "tr.ahaber",
    "Ulusal Kanal":    "tr.ulusalkanal",
    "Bloomberg HT":    "tr.bloomberght",
    "CNBC-e":          "tr.cnbce",
    "Habertürk":       "tr.haberturk",
    "Haberturk":       "tr.haberturk",
    # Spor
    "TRT Spor":        "tr.trtspor",
    "TRT Spor Yıldız": "tr.trtsporyildiz",
    "TRT Spor Yildiz": "tr.trtsporyildiz",
    "A Spor":          "tr.aspor",
    "HT Spor":         "tr.htspor",
    "Ekol Sports":     "tr.ekolsports",
    "Tivibu Spor":     "tr.tivibuspor",
    # Egitim/Genel
    "TRT 2":           "tr.trt2",
    "TLC":             "tr.tlc",
    "DMAX":            "tr.dmax",
    "D Max":           "tr.dmax",
    # Belgesel
    "TRT Belgesel":    "tr.trtbelgesel",
    # Muzik
    "Dream Türk":      "tr.dreamturk",
    "Dream Turk":      "tr.dreamturk",
}


def fetch_source_playlist():
    """uzunmuhalefet.com playlist'ini indir, {tvg-id: stream_url} donur."""
    print(f"Kaynak playlist indiriliyor: {SOURCE_M3U}")
    try:
        r = requests.get(SOURCE_M3U, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        r.raise_for_status()
    except Exception as e:
        print(f"  !! Kaynak indirilemedi: {e}")
        return {}

    lines   = r.text.splitlines()
    result  = {}   # tvg-id -> stream url
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('#EXTINF'):
            # Kanal adini al
            name_m = re.search(r',(.+)$', line)
            name   = name_m.group(1).strip() if name_m else ''
            # URL'yi al
            j = i + 1
            while j < len(lines) and lines[j].startswith('#'):
                j += 1
            url = lines[j] if j < len(lines) and lines[j].startswith('http') else ''

            # Kendi CHANNEL_MAP'imize gore eslestir
            our_id = CHANNEL_MAP.get(name)
            if our_id and url:
                result[our_id] = url
                print(f"  eslesti: {name:25s} -> {our_id} -> {url[:60]}...")
        i += 1

    print(f"Toplam {len(result)} kanal eslesti.")
    return result


def main():
    source = fetch_source_playlist()
    if not source:
        print("Kaynak bos, cikiliyor.")
        return

    lines   = PLAYLIST.read_text(encoding='utf-8').splitlines()
    updated = 0

    for i, line in enumerate(lines):
        if not line.startswith('#EXTINF:'):
            continue
        tvg_m = re.search(r'tvg-id="([^"]+)"', line)
        if not tvg_m:
            continue
        tvg_id = tvg_m.group(1)
        if tvg_id not in source:
            continue

        new_url = source[tvg_id]

        # Bir sonraki http satiri
        j = i + 1
        while j < len(lines) and lines[j].startswith('#') and not lines[j].startswith('#EXTINF'):
            j += 1
        if j < len(lines) and lines[j].startswith('http'):
            cur = lines[j]
            # Sadece tvkulesi/kavuntv URL'lerini degistir (medya.trt, daioncdn, youtube vs. koru)
            if ('tvkulesi' in cur or 'kavuntv' in cur) and cur != new_url:
                lines[j] = new_url
                updated += 1

    PLAYLIST.write_text('\n'.join(lines), encoding='utf-8')
    print(f"\nTamamlandi: {updated} URL guncellendi")


if __name__ == '__main__':
    main()
