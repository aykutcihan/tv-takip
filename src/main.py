"""
Ana orkestratör:
  config yükle -> her kanal için kaynakları öncelik sırasıyla çek
  -> merge -> bitiş türet -> TMDb film zenginleştir -> kaynaksızsa placeholder
  -> deterministik epg.xml yaz.

Çalıştır:  python src/main.py
"""
from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime, timedelta

import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from models import Channel, Programme
from adapters import build_registry, split_source
from merge import merge_sources
from normalize import derive_stops, ist
from enrich_tmdb import TMDbEnricher
from placeholder import placeholder_programmes
from xmltv import write_xmltv
from json_epg import write_json_epg

ROOT = Path(__file__).resolve().parent.parent


def load_yaml(p):
    return yaml.safe_load(Path(p).read_text("utf-8"))


def main():
    settings = load_yaml(ROOT / "config/settings.yaml")
    chans_cfg = load_yaml(ROOT / "config/channels.yaml")["channels"]

    session = requests.Session()
    registry = build_registry(session)
    tmdb = TMDbEnricher(settings.get("tmdb", {}))

    channels, all_progs = [], []

    for tvg_id, c in chans_cfg.items():
        ch = Channel(id=tvg_id, name=c.get("name", tvg_id),
                     sources=c.get("sources", []))
        channels.append(ch)

        per_source = []
        for src in ch.sources:
            prefix, sid = split_source(src)
            adapter = registry.get(prefix)
            if not adapter:
                print(f"[uyarı] bilinmeyen kaynak: {prefix}")
                continue
            try:
                progs = adapter.fetch(sid, tvg_id)
                progs = derive_stops(progs)  # tvyayinakisi/digiturk bitişini doldur
                if progs:
                    per_source.append(progs)
                    print(f"  {tvg_id} <- {src}: {len(progs)} program")
            except Exception as e:
                print(f"  [hata] {tvg_id} <- {src}: {e}")

        if per_source:
            merged = merge_sources(
                per_source,
                settings.get("min_gap_minutes", 2),
                settings.get("overlap_tolerance_minutes", 5))
            merged = derive_stops(merged)
            # beIN kanalları: son programdan sonra yeni veri gelene kadar aynı günü döngüyle tekrarla
            if merged and "bein" in tvg_id.lower():
                last = max(merged, key=lambda p: p.start)
                if last.stop:
                    loop_end = last.stop + timedelta(hours=24)
                    sorted_progs = sorted(
                        [p for p in merged if p.stop and p.source != "loop"],
                        key=lambda p: p.start)
                    if sorted_progs:
                        cur = last.stop
                        while cur < loop_end:
                            offset = cur - sorted_progs[0].start
                            for p in sorted_progs:
                                ns = p.start + offset
                                ne = p.stop + offset
                                if ns >= loop_end:
                                    break
                                merged.append(Programme(
                                    channel_id=tvg_id,
                                    start=ns,
                                    stop=min(ne, loop_end),
                                    title=p.title,
                                    desc=p.desc,
                                    category=p.category,
                                    source="loop",
                                ))
                            cur = cur + (sorted_progs[-1].stop - sorted_progs[0].start)
        else:
            merged = placeholder_programmes(
                tvg_id, settings.get("window_days", 7))
            print(f"  {tvg_id}: kaynak yok -> placeholder")

        all_progs.extend(merged)

    # film zenginleştirme
    tmdb.enrich(all_progs)
    tmdb.save()

    # Sadece playlist'teki kanalları dahil et
    import re as _re
    playlist_path = ROOT / "playlist.m3u"
    if playlist_path.exists():
        playlist_ids = set(_re.findall(r'tvg-id="([^"]+)"', playlist_path.read_text(encoding="utf-8")))
        playlist_ids.discard("")
        channels = [c for c in channels if c.id in playlist_ids]
        all_progs = [p for p in all_progs if p.channel_id in playlist_ids]
        print(f"Playlist filtresi: {len(channels)} kanal, {len(all_progs)} program kaldi")

    xml = write_xmltv(
        channels, all_progs,
        tz_offset=settings.get("tz_offset", "+0300"),
        generator=settings.get("generator_name", "kisisel-epg"))

    out = ROOT / settings.get("output_path", "epg.xml")
    out.write_text(xml, "utf-8")
    print(f"\nYazıldı: {out}  ({len(channels)} kanal, {len(all_progs)} program)")

    # Kanal bazli JSON EPG
    write_json_epg(channels, all_progs, ROOT / "epg")


if __name__ == "__main__":
    main()
