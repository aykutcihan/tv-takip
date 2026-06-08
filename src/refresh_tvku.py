"""
streams.uzunmuhalefet.com uzerinden Turk kanallarinin uzunmuhalefet URL'lerini
mevcut playlist'e YENI ENTRY olarak ekler — mevcut URL'leri degistirmez.
Bot tespiti yok, Playwright gerektirmez.
"""
import sys, io, re, requests, warnings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
warnings.filterwarnings('ignore')
from pathlib import Path

ROOT     = Path(__file__).resolve().parent.parent
PLAYLIST = ROOT / "playlist.m3u"

SOURCE_M3U = "https://streams.uzunmuhalefet.com/lists/tr.m3u"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'tr-TR,tr;q=0.9',
}

def normalize(s):
    s = s.lower()
    for a, b in [('ü','u'),('ı','i'),('ö','o'),('ş','s'),('ç','c'),('ğ','g')]:
        s = s.replace(a, b)
    return re.sub(r'[^a-z0-9]', '', s)


def fetch_source():
    """uzunmuhalefet playlist -> {normalize(name): (name, logo, url)}"""
    print(f"Kaynak indiriliyor: {SOURCE_M3U}")
    try:
        r = requests.get(SOURCE_M3U, timeout=30, headers=HEADERS)
        r.raise_for_status()
    except Exception as e:
        print(f"  !! {e}")
        return {}

    result, i = {}, 0
    lines = r.text.splitlines()
    while i < len(lines):
        if lines[i].startswith('#EXTINF'):
            m_name = re.search(r',(.+)$', lines[i])
            m_logo = re.search(r'tvg-logo="([^"]*)"', lines[i])
            name = m_name.group(1).strip() if m_name else ''
            logo = m_logo.group(1) if m_logo else ''
            j = i + 1
            while j < len(lines) and lines[j].startswith('#'):
                j += 1
            url = lines[j] if j < len(lines) and lines[j].startswith('http') else ''
            if name and url:
                result[normalize(name)] = (name, logo, url)
        i += 1

    print(f"  Kaynak: {len(result)} kanal.")
    return result


def main():
    source = fetch_source()
    if not source:
        return

    content = PLAYLIST.read_text(encoding='utf-8')
    lines   = content.splitlines()

    added     = 0
    skipped   = 0
    not_found = []

    for norm_key, (src_name, src_logo, proxy_url) in source.items():
        # Playlist'te bu kanal var mi?
        matched_indices = []
        for i, line in enumerate(lines):
            if not line.startswith('#EXTINF:'):
                continue
            m = re.search(r',(.+)$', line)
            if not m:
                continue
            if normalize(m.group(1).strip()) == norm_key:
                matched_indices.append(i)

        if not matched_indices:
            not_found.append(src_name)
            continue

        # "Uzun" grubundaki eslesmeler haric tut
        matched_indices = [i for i in matched_indices
                           if 'group-title="Uzun"' not in lines[i]]
        if not matched_indices:
            skipped += 1
            continue

        # Son eslesen EXTINF'in URL'sinden sonraya ekle
        last_i = matched_indices[-1]
        j = last_i + 1
        while j < len(lines) and lines[j].startswith('#') and not lines[j].startswith('#EXTINF'):
            j += 1
        # j simdi URL satirinda
        if j < len(lines) and lines[j].startswith('http'):
            # Bu kanalin herhangi bir satirinda uzunmuhalefet URL'si zaten var mi?
            # Bir sonraki FARKLI kanala kadar tara
            already = False
            k = j + 1
            while k < len(lines):
                if lines[k].startswith('#EXTINF:') and f'tvg-id="{lines[last_i]}"' not in lines[k]:
                    break
                if 'uzunmuhalefet.com' in lines[k]:
                    already = True
                    break
                k += 1
            if already:
                skipped += 1
                continue

            # Mevcut URL'nin hemen altina yeni entry ekle
            # Orijinal EXTINF satirini kopyala, sadece source ekle
            orig_extinf = lines[last_i]
            new_extinf  = orig_extinf  # ayni grup, logo, tvg-id
            insert_pos  = j + 1

            lines.insert(insert_pos,     '')
            lines.insert(insert_pos + 1, f'# {src_name},    source: uzunmuhalefet')
            lines.insert(insert_pos + 2, new_extinf)
            lines.insert(insert_pos + 3, proxy_url)
            added += 1
            print(f"  + {src_name}")

    PLAYLIST.write_text('\n'.join(lines), encoding='utf-8')
    print(f"\nEklendi: {added} | Zaten var: {skipped} | Bulunamadi: {len(not_found)}")
    if not_found:
        print("\nPlaylist'te BULUNAMAYAN kanallar (eklemek ister misiniz?):")
        for ch in not_found:
            print(f"  - {ch}")


if __name__ == '__main__':
    main()
