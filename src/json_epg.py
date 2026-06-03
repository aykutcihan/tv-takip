"""
Kanal bazli EPG JSON dosyalari uretir.
Her kanal icin epg/{channel-id}.json yazar.
Format: { "channel": "tr.trt1", "updated": "ISO", "programmes": [...] }
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import List

from models import Programme, Channel
from normalize import to_xmltv


def _prog_to_dict(p: Programme) -> dict:
    d = {
        "start": p.start.isoformat() if p.start else None,
        "stop":  p.stop.isoformat()  if p.stop  else None,
        "title": p.title or "",
    }
    if p.sub_title: d["subTitle"] = p.sub_title
    if p.desc:      d["desc"]     = p.desc
    if p.category:  d["category"] = p.category
    if p.year:      d["year"]     = p.year
    if p.actors:    d["actors"]   = p.actors
    return d


def write_json_epg(channels: List[Channel],
                   programmes: List[Programme],
                   output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    updated = datetime.utcnow().isoformat() + "Z"

    # Kanal bazli grupla
    by_channel: dict[str, list] = {ch.id: [] for ch in channels}
    for p in programmes:
        if p.channel_id in by_channel and p.stop:
            by_channel[p.channel_id].append(_prog_to_dict(p))

    # Her kanal icin dosya yaz
    written = 0
    for ch in channels:
        progs = sorted(by_channel.get(ch.id, []), key=lambda x: x["start"] or "")
        data = {
            "channel": ch.id,
            "name":    ch.name,
            "updated": updated,
            "programmes": progs,
        }
        out_file = output_dir / f"{ch.id}.json"
        out_file.write_text(
            json.dumps(data, ensure_ascii=False, separators=(',', ':')),
            encoding="utf-8"
        )
        written += 1

    # Index dosyasi - tum kanal listesi
    index = {
        "updated": updated,
        "channels": [
            {"id": ch.id, "name": ch.name, "count": len(by_channel.get(ch.id, []))}
            for ch in sorted(channels, key=lambda c: c.id)
        ]
    }
    (output_dir / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, separators=(',', ':')),
        encoding="utf-8"
    )
    print(f"JSON EPG yazildi: {written} kanal -> {output_dir}/")
