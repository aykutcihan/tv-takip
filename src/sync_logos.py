"""
config/logos.yaml'daki tvg-id: logo_url eslesimini playlist.m3u'ya uygular.
EPG workflow'undan veya tek basina calistirilabilir.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
LOGOS_YAML = ROOT / 'config' / 'logos.yaml'
PLAYLIST = ROOT / 'playlist.m3u'


def load_logos() -> dict[str, str]:
    data = yaml.safe_load(LOGOS_YAML.read_text(encoding='utf-8'))
    return {k: v for k, v in data.get('logos', {}).items() if v}


def sync(dry_run: bool = False) -> int:
    logos = load_logos()
    lines = PLAYLIST.read_text(encoding='utf-8').splitlines()
    updated = 0

    for i, line in enumerate(lines):
        if not line.startswith('#EXTINF:'):
            continue
        id_m = re.search(r'tvg-id="([^"]*)"', line)
        if not id_m:
            continue
        ch_id = id_m.group(1)
        if ch_id not in logos:
            continue

        new_logo = logos[ch_id]
        logo_m = re.search(r'tvg-logo="([^"]*)"', line)
        current = logo_m.group(1) if logo_m else ''
        if current == new_logo:
            continue

        if 'tvg-logo=' in line:
            lines[i] = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{new_logo}"', line)
        else:
            lines[i] = line.replace('#EXTINF:-1 ', f'#EXTINF:-1 tvg-logo="{new_logo}" ', 1)
        updated += 1

    if updated and not dry_run:
        PLAYLIST.write_text('\n'.join(lines), encoding='utf-8')

    return updated


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    n = sync()
    print(f'{n} kanalin logosu guncellendi')
