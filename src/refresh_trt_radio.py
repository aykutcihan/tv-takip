"""
TRT radyo stream URL'lerini trtdinle.com API'den yeniler.
playlist.m3u'daki trt.radyo.* tvg-id'li kanalları günceller.
"""
import sys, io, re, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAYLIST = ROOT / "playlist.m3u"
API_URL = "https://www.trtdinle.com/api/channels"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
SKIP = {"TRT 1", "TRT 2", "TRT Müzik", "TRT World"}


def main():
    print("TRT radyo URL'leri yenileniyor...")
    r = requests.get(API_URL, headers=HEADERS, timeout=15)
    channels = r.json().get("channels", [])

    # slug -> stream URL haritasi
    stream_map = {}
    for ch in channels:
        title = ch.get("title", "")
        audio = ch.get("audio")
        if not audio or not audio.get("url") or title in SKIP:
            continue
        path = ch.get("path", "")
        slug = path.replace("/channel/", "").replace("/", "")
        stream_map[f"trt.radyo.{slug}"] = audio["url"]

    lines = PLAYLIST.read_text(encoding="utf-8").splitlines()
    updated = 0
    for i, line in enumerate(lines):
        if line.startswith("#EXTINF:"):
            m = re.search(r'tvg-id="(trt\.radyo\.[^"]+)"', line)
            if m and i + 1 < len(lines):
                tvg_id = m.group(1)
                new_url = stream_map.get(tvg_id)
                if new_url and lines[i + 1] != new_url:
                    lines[i + 1] = new_url
                    updated += 1
                    print(f"  ok {tvg_id}")

    PLAYLIST.write_text("\n".join(lines), encoding="utf-8")
    print(f"Tamamlandi: {updated} URL guncellendi")


if __name__ == "__main__":
    main()
