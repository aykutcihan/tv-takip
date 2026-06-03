"""
Karnaval radyo istasyonlarini aylik gunceller.
Yeni istasyon eklenmisse playlist'e ekler, URL degismisse gunceller.
"""
import sys, io, re, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAYLIST = ROOT / "playlist.m3u"
API_URL = "https://newapi.karnaval.com/station?activeOn=web"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Referer": "https://karnaval.com/"}


def main():
    print("Karnaval radyo istasyonlari guncelleniyor...")
    r = requests.get(API_URL, headers=HEADERS, timeout=15)
    stations = r.json().get("data", {}).get("stations", [])
    print(f"  {len(stations)} istasyon bulundu")

    lines = PLAYLIST.read_text(encoding="utf-8").splitlines()

    # Mevcut karnaval tvg-id'leri
    existing = {}
    for i, line in enumerate(lines):
        if line.startswith("#EXTINF:"):
            m = re.search(r'tvg-id="(karnaval\.\d+)"', line)
            if m and i + 1 < len(lines):
                existing[m.group(1)] = i

    added = 0
    updated = 0

    for s in stations:
        mount = s.get("mount") or s.get("streamUrlAac")
        if not mount:
            continue
        name = s.get("name", "")
        logo = s.get("smallLogoUrl") or s.get("logoUrl") or ""
        tvg_id = f"karnaval.{s['id']}"
        stream_url = f"https://playerservices.streamtheworld.com/api/livestream-redirect/{mount}.mp3"

        if tvg_id in existing:
            i = existing[tvg_id]
            if lines[i + 1] != stream_url:
                lines[i + 1] = stream_url
                updated += 1
                print(f"  ~ {name}")
        else:
            lines.append(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo}" group-title="Radyo",{name}')
            lines.append(stream_url)
            added += 1
            print(f"  + {name}")

    PLAYLIST.write_text("\n".join(lines), encoding="utf-8")
    print(f"Tamamlandi: {added} yeni, {updated} guncellendi")


if __name__ == "__main__":
    main()
