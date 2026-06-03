"""
YouTube canli yayin URL'lerini yenile.
yt-dlp ile her saat taze HLS URL alir ve playlist.m3u'ya yazar.

Eklemek icin channels.yaml'a YOUTUBE_CHANNELS'a ekle:
  tvg_id: youtube_video_id
"""
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAYLIST = ROOT / "playlist.m3u"

# tvg-id → YouTube video ID (canli yayin)
YOUTUBE_CHANNELS = {
    "tr.ekoturk":           "5ovykCkBWfU",
    "tr.cnbce":             "aZ3ycSbSYBA",
    "tr.seksenler":         "qGYlF1MiMxw",
    "tr.leylaileMecnun":    "3nlND4audLg",
    "tr.yedinumara":        "rS5dHYQsSxs",
    "tr.kemalsunal":        "mq4GiHzxZwk",
    "tr.kralakustik":       "O_-NjHABJIg",
    "tr.tgrtbelgesel":      "32y7IEtD5OU",
    "tr.eurod.yt":          "DWTZdz4LQbY",
    "tr.atv.yt":            "n7HUV-KUDfE",
    "tr.startv.yt":         "82O6yOy_XwE",
    "tr.showtv.yt":         "ouuCjEjyKVI",
    "tr.nowtv.yt":          "8vlyTcrcchc",
    "tr.a2tv.yt":           "HtnytvwXi5o",
    "tr.tv2.yt":            "A32ePdlFt7U",
    "tr.showmax.yt":        "Y3vGHFrsqrs",
    "tr.guldurguldur":      "Jv8HS8gqV78",
    "tr.arzufilm":          "RqegY0WKtZA",
    "tr.gulsahkemal":       "tWWFY5lf1U0",
    "tr.sabana2":           "VkXvDzJyUQs",
    "tr.yesilcam":          "cKVuxje7YqA",
    "tr.beinsporthaber.yt": "i7UpPgxfZZ8",
    "tr.aspor.yt":          "mgeW8Qm8-SY",
    "tr.ntv.yt":            "pqq5c6k70kk",
    "tr.sozcu.yt":          "ztmY_cCtUl0",
    "tr.cicektaksi":        "6SkIsrCIPfQ",
    "tr.tele2haber":       "LXWokI7M9HE",
    "tr.bizimevtv":        "GRLd2oYZFnM",
    "tr.krttv":            "LBffKHlCx8U",
}


def get_youtube_stream(video_id: str) -> str | None:
    """yt-dlp ile YouTube canli yayin HLS URL'ini al."""
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--get-url",
                "-f", "b",
                "--no-warnings",
                f"https://www.youtube.com/watch?v={video_id}",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        url = result.stdout.strip().split("\n")[0]
        if url and "googlevideo.com" in url:
            return url
    except Exception as e:
        print(f"  [youtube] {video_id} hata: {e}")
    return None


def main():
    print("YouTube stream URL'leri yenileniyor...")

    content = PLAYLIST.read_text(encoding="utf-8")
    lines = content.splitlines()
    updated = 0

    for tvg_id, video_id in YOUTUBE_CHANNELS.items():
        stream_url = get_youtube_stream(video_id)
        if not stream_url:
            print(f"  {tvg_id}: URL alinamadi")
            continue

        prev = updated
        for i, line in enumerate(lines):
            if f'tvg-id="{tvg_id}"' in line:
                # Sonraki URL satırını bul (# source satırını atla)
                j = i + 1
                while j < len(lines) and lines[j].startswith('#'):
                    j += 1
                if j < len(lines) and lines[j].startswith('http'):
                    lines[j] = stream_url
                updated += 1

        if updated > prev:
            print(f"  {tvg_id}: {stream_url[:70]}...")

    PLAYLIST.write_text("\n".join(lines), encoding="utf-8")
    print(f"Guncellendi: {updated} kanal")


if __name__ == "__main__":
    main()
