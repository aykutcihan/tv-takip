"""
Radyo EPG üreticisi.
config/radios.yaml'daki kanallar için EPG çeker, radios.xml yazar.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import yaml
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent
from adapters.trtradyo import TRTRadyoAdapter

ROOT = Path(__file__).resolve().parent.parent
RADIOS_YAML = ROOT / "config" / "radios.yaml"
OUTPUT = ROOT / "radios.xml"


def write_xmltv(radios: dict, all_programmes: list) -> None:
    tv = Element("tv", attrib={"generator-info-name": "kisisel-epg-radyo"})

    for tvg_id, info in radios.items():
        ch = SubElement(tv, "channel", id=tvg_id)
        dn = SubElement(ch, "display-name", lang="tr")
        dn.text = info["name"]
        if info.get("logo"):
            SubElement(ch, "icon", src=info["logo"])

    for prog in sorted(all_programmes, key=lambda p: p.start):
        if prog.stop is None:
            continue
        attrs = {
            "start": prog.start.strftime("%Y%m%d%H%M%S %z"),
            "stop":  prog.stop.strftime("%Y%m%d%H%M%S %z"),
            "channel": prog.channel_id,
        }
        p = SubElement(tv, "programme", attrib=attrs)
        t = SubElement(p, "title", lang="tr")
        t.text = prog.title

    indent(tv, space="  ")
    tree = ElementTree(tv)
    tree.write(str(OUTPUT), encoding="utf-8", xml_declaration=True)
    print(f"radios.xml yazildi: {len(all_programmes)} program, {len(radios)} radyo")


def main():
    config = yaml.safe_load(RADIOS_YAML.read_text(encoding="utf-8"))
    radios = config.get("radios", {})
    print(f"Radyo sayisi: {len(radios)}")

    adapter = TRTRadyoAdapter()
    all_programmes = []

    for tvg_id, info in radios.items():
        sources = info.get("sources", [])
        for source in sources:
            prefix, _, source_id = source.partition(":")
            if prefix == "trtradyo":
                print(f"  {info['name']}...")
                progs = adapter.fetch(source_id, tvg_id)
                all_programmes.extend(progs)
                print(f"    {len(progs)} program")
                break

    write_xmltv(radios, all_programmes)


if __name__ == "__main__":
    main()
