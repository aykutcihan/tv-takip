"""Deterministik XMLTV yazıcı. Stabil sıra -> değişiklik tespiti çalışsın."""
from __future__ import annotations
from typing import List
from xml.sax.saxutils import escape

from models import Programme, Channel
from normalize import to_xmltv


def _el(tag, text, lang="tr"):
    return f'    <{tag} lang="{lang}">{escape(text)}</{tag}>\n'


def write_xmltv(channels: List[Channel],
                programmes: List[Programme],
                tz_offset: str = "+0300",
                generator: str = "kisisel-epg") -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>\n']
    lines.append(f'<tv generator-info-name="{escape(generator)}">\n')

    # kanallar (id'ye göre sıralı)
    for ch in sorted(channels, key=lambda c: c.id):
        lines.append(f'  <channel id="{escape(ch.id)}">\n')
        lines.append(f'    <display-name>{escape(ch.name)}</display-name>\n')
        lines.append('  </channel>\n')

    # programlar (kanal, start'a göre sıralı -> deterministik)
    for p in sorted(programmes, key=lambda x: (x.channel_id, x.start)):
        if not p.stop:
            continue
        s = to_xmltv(p.start, tz_offset)
        e = to_xmltv(p.stop, tz_offset)
        lines.append(
            f'  <programme start="{s}" stop="{e}" channel="{escape(p.channel_id)}">\n')
        lines.append(_el("title", p.title or ""))
        if p.sub_title:
            lines.append(_el("sub-title", p.sub_title))
        if p.desc:
            lines.append(_el("desc", p.desc))
        if p.category:
            lines.append(_el("category", p.category))
        if p.year:
            lines.append(f'    <date>{p.year}</date>\n')
        if p.actors:
            lines.append('    <credits>\n')
            for actor in p.actors:
                lines.append(f'      <actor>{escape(actor)}</actor>\n')
            lines.append('    </credits>\n')
        lines.append('  </programme>\n')

    lines.append('</tv>\n')
    return "".join(lines)
