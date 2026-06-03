"""
channels.yaml'daki logo: alanlarını playlist.m3u'ya tvg-id üzerinden uygular.
EPG workflow'undan veya tek başına çalıştırılabilir.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CHANNELS_YAML = ROOT / 'config' / 'channels.yaml'
PLAYLIST = ROOT / 'playlist.m3u'


def load_logo_map() -> dict[str, str]:
    data = yaml.safe_load(CHANNELS_YAML.read_text(encoding='utf-8'))
    return {
        ch_id: ch.get('logo', '')
        for ch_id, ch in data.get('channels', {}).items()
        if ch.get('logo')
    }


def sync(dry_run: bool = False) -> int:
    logo_map = load_logo_map()
    lines = PLAYLIST.read_text(encoding='utf-8').splitlines()
    updated = 0

    for i, line in enumerate(lines):
        if not line.startswith('#EXTINF:'):
            continue
        tvg_id_m = re.search(r'tvg-id="([^"]*)"', line)
        if not tvg_id_m:
            continue
        ch_id = tvg_id_m.group(1)
        if ch_id not in logo_map:
            continue

        new_logo = logo_map[ch_id]
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
