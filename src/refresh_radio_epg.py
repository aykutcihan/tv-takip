"""
Radyo EPG'sini gunceller.
- Karnaval: su an calani ceker, 4 saatlik blok yazar
- TRT: trtdinle.com'dan program akisi ceker
Her 5 dakikada bir calisir.
"""
import sys, io, re, requests, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from datetime import datetime, timedelta
from dateutil import tz
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent
import yaml

ROOT = Path(__file__).resolve().parent.parent
RADIOS_YAML = ROOT / "config" / "radios.yaml"
OUTPUT = ROOT / "radios.xml"
IST = tz.gettz("Europe/Istanbul")

KARNAVAL_STATION_API = "https://newapi.karnaval.com/station?activeOn=web"
KARNAVAL_SONG_API    = "https://karnaval.com/functions/v6/api.functions.php"
KARNAVAL_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://karnaval.com/",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/json; charset=UTF-8",
}


def get_karnaval_now_playing() -> dict:
    """station_id -> {title, artist, album_cover, start, end}"""
    try:
        r = requests.put(KARNAVAL_SONG_API, headers=KARNAVAL_HEADERS,
            json={"command": "get_current_song", "station_id": "all",
                  "lastVersion": 0, "custom_k_parameter": "karnaval_web_v6"},
            timeout=10)
        data = r.json()
        if not data.get("result"):
            return {}
        return data.get("data", {})
    except Exception as e:
        print(f"  [karnaval] now-playing hatasi: {e}")
        return {}


def get_karnaval_stations() -> dict:
    """station_id (int) -> {name, mount, logo}"""
    try:
        r = requests.get(KARNAVAL_STATION_API, headers=KARNAVAL_HEADERS, timeout=10)
        stations = r.json().get("data", {}).get("stations", [])
        return {str(s["id"]): s for s in stations}
    except Exception as e:
        print(f"  [karnaval] stations hatasi: {e}")
        return {}


def build_programme(tvg_id: str, title: str, artist: str, cover: str,
                    start: datetime, stop: datetime) -> Element:
    p = Element("programme", attrib={
        "start": start.strftime("%Y%m%d%H%M%S %z"),
        "stop":  stop.strftime("%Y%m%d%H%M%S %z"),
        "channel": tvg_id,
    })
    t = SubElement(p, "title", lang="tr")
    t.text = f"{artist} - {title}" if artist else title
    if cover:
        SubElement(p, "icon", src=cover)
    return p


def make_placeholder(tvg_id: str, start: datetime, stop: datetime) -> Element:
    p = Element("programme", attrib={
        "start": start.strftime("%Y%m%d%H%M%S %z"),
        "stop":  stop.strftime("%Y%m%d%H%M%S %z"),
        "channel": tvg_id,
    })
    t = SubElement(p, "title", lang="tr")
    t.text = "Müzik Yayını"
    return p


def karnaval_programmes(stations: dict, songs: dict) -> list:
    """station_N key -> karnaval.ID tvg_id eslesmesi yap"""
    # Station list sira numarasiyla eslestir
    station_list = list(stations.values())
    programmes = []
    now = datetime.now(tz=IST)
    window_end = now + timedelta(hours=4)

    for song_key, song in songs.items():
        try:
            num = int(song_key.replace("station_", "")) - 1
        except ValueError:
            continue  # station_5SC010_SO1 gibi sub-channel key'leri atla
        if num >= len(station_list):
            continue
        station = station_list[num]
        tvg_id = f"karnaval.{station['id']}"

        # Suanki sarki
        duration_sec = int(song.get("duration_sec") or 0)
        progress_sec = int(song.get("progress") or 0)
        title  = song.get("title", "")
        artist = song.get("artist", "")
        cover  = song.get("album_cover_art", "")

        if duration_sec > 0 and title:
            song_start = now - timedelta(seconds=progress_sec)
            song_end   = song_start + timedelta(seconds=duration_sec)
            if song_end < now:
                song_end = now + timedelta(minutes=4)
            programmes.append(build_programme(tvg_id, title, artist, cover, song_start, song_end))
            # Sarki bitisinden 4 saat sonrasina kadar placeholder
            ph_start = song_end
        else:
            ph_start = now

        # Placeholder bloklari (30 dakikalik)
        cur = ph_start
        while cur < window_end:
            block_end = min(cur + timedelta(minutes=30), window_end)
            programmes.append(make_placeholder(tvg_id, cur, block_end))
            cur = block_end

    return programmes


def trt_programmes() -> list:
    """TRT radyo EPG'sini trtdinle.com'dan cek."""
    try:
        from adapters.trtradyo import TRTRadyoAdapter, RADIO_CHANNELS
        adapter = TRTRadyoAdapter()
        progs = []
        config = yaml.safe_load(RADIOS_YAML.read_text(encoding="utf-8"))
        for tvg_id, info in config.get("radios", {}).items():
            if not tvg_id.startswith("trt.radyo."):
                continue
            for source in info.get("sources", []):
                prefix, _, sid = source.partition(":")
                if prefix == "trtradyo":
                    fetched = adapter.fetch(sid, tvg_id)
                    progs.extend(fetched)
                    break
        return progs
    except Exception as e:
        print(f"  [trt] epg hatasi: {e}")
        return []


def write_xmltv(radios: dict, programmes: list) -> None:
    tv = Element("tv", attrib={"generator-info-name": "kisisel-epg-radyo"})

    for tvg_id, info in radios.items():
        ch = SubElement(tv, "channel", id=tvg_id)
        dn = SubElement(ch, "display-name", lang="tr")
        dn.text = info["name"]
        if info.get("logo"):
            SubElement(ch, "icon", src=info["logo"])

    # Karnaval kanallar icin channel elementi
    try:
        r = requests.get(KARNAVAL_STATION_API, headers=KARNAVAL_HEADERS, timeout=10)
        karnaval_stations = r.json().get("data", {}).get("stations", [])
        for s in karnaval_stations:
            ch = SubElement(tv, "channel", id=f"karnaval.{s['id']}")
            dn = SubElement(ch, "display-name", lang="tr")
            dn.text = s.get("name", "")
            logo = s.get("smallLogoUrl") or s.get("logoUrl") or ""
            if logo:
                SubElement(ch, "icon", src=logo)
    except Exception:
        pass

    from xml.etree.ElementTree import Element as _Elem
    def _sort_key(p):
        if isinstance(p, _Elem):
            return (p.get("channel", ""), p.get("start", ""))
        return (getattr(p, "channel_id", ""), str(getattr(p, "start", "")))

    for prog in sorted(programmes, key=_sort_key):
        if isinstance(prog, _Elem):
            tv.append(prog)
        else:
            # Programme nesnesi -> XML'e cevir
            if not prog.stop:
                continue
            attrs = {
                "start":   prog.start.strftime("%Y%m%d%H%M%S %z"),
                "stop":    prog.stop.strftime("%Y%m%d%H%M%S %z"),
                "channel": prog.channel_id,
            }
            p_el = SubElement(tv, "programme", attrib=attrs)
            t = SubElement(p_el, "title", lang="tr")
            t.text = prog.title or ""

    indent(tv, space="  ")
    ElementTree(tv).write(str(OUTPUT), encoding="utf-8", xml_declaration=True)
    print(f"radios.xml yazildi: {len(programmes)} program")


def main():
    print("Radyo EPG guncelleniyor...")
    config = yaml.safe_load(RADIOS_YAML.read_text(encoding="utf-8"))
    radios = config.get("radios", {})

    # TRT
    print("TRT radyo EPG...")
    trt_progs = trt_programmes()
    print(f"  {len(trt_progs)} program")

    # Karnaval
    print("Karnaval now-playing...")
    stations = get_karnaval_stations()
    songs    = get_karnaval_now_playing()
    krnv_progs = karnaval_programmes(stations, songs)
    print(f"  {len(krnv_progs)} program blogu")

    write_xmltv(radios, trt_progs + krnv_progs)


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).resolve().parent)
    main()
