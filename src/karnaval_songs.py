"""
Karnaval'dan su an calani ceker, karnaval-songs.json yazar.
radio-epg workflow'undan cagirilir (5 dakikada bir).
"""
import sys, io, json, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path

ROOT   = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "karnaval-songs.json"

STATION_API = "https://newapi.karnaval.com/station?activeOn=web"
SONG_API    = "https://karnaval.com/functions/v6/api.functions.php"
HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer":         "https://karnaval.com/",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type":    "application/json; charset=UTF-8",
}


def main():
    # Bulk API - station_N key'i direkt ID'ye esler (station_4 = karnaval.4)
    r2 = requests.put(SONG_API, headers=HEADERS, timeout=10, json={
        "command": "get_current_song",
        "station_id": "all",
        "lastVersion": 0,
        "custom_k_parameter": "karnaval_web_v6",
    })
    data = r2.json()
    if not data.get("result"):
        print("Veri alinamadi")
        return

    result = {}
    for key, song in data["data"].items():
        try:
            num = int(key.replace("station_", ""))
        except ValueError:
            continue  # station_5SC010_SO1 gibi sub-channel key'leri atla
        tvg_id = f"karnaval.{num}"  # station_4 -> karnaval.4 (JoyTurk)
        if song.get("title"):
            result[tvg_id] = {
                "title":    song.get("title", ""),
                "artist":   song.get("artist", ""),
                "cover":    song.get("album_cover_art", ""),
                "progress": song.get("progress", 0),
                "duration": song.get("duration_sec", 0),
            }

    OUTPUT.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    print(f"karnaval-songs.json yazildi: {len(result)} istasyon")


if __name__ == "__main__":
    main()
