"""
channels.yaml'daki logo: alanlarini playlist.m3u'ya uygular.
Once tvg-id ile eslestirir, tvg-id bos ise kanal adiyla fallback yapar.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CHANNELS_YAML = ROOT / 'config' / 'channels.yaml'
PLAYLIST = ROOT / 'playlist.m3u'


def load_maps() -> tuple[dict[str, str], dict[str, str]]:
    data = yaml.safe_load(CHANNELS_YAML.read_text(encoding='utf-8'))
    by_id: dict[str, str] = {}
    by_name: dict[str, str] = {}
    for ch_id, ch in data.get('channels', {}).items():
        logo = ch.get('logo', '')
        if not logo:
            continue
        by_id[ch_id] = logo
        name = ch.get('name', '')
        if name:
            by_name[name] = logo
    return by_id, by_name


def sync(dry_run: bool = False) -> int:
    by_id, by_name = load_maps()
    lines = PLAYLIST.read_text(encoding='utf-8').splitlines()
    updated = 0

    for i, line in enumerate(lines):
        if not line.startswith('#EXTINF:'):
            continue

        # Mevcut logoyu kontrol et
        logo_m = re.search(r'tvg-logo="([^"]*)"', line)
        current = logo_m.group(1) if logo_m else ''
        if current:
            continue  # zaten logosu var, dokunma

        # tvg-id ile eslestir
        id_m = re.search(r'tvg-id="([^"]*)"', line)
        ch_id = id_m.group(1) if id_m else ''
        new_logo = by_id.get(ch_id, '') if ch_id else ''

        # tvg-id yoksa veya eslesmiyorsa isimle dene
        if not new_logo:
            name_m = re.search(r',(.+)$', line)
            name = name_m.group(1).strip() if name_m else ''
            new_logo = by_name.get(name, '')

        if not new_logo:
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
