"""
Merge motoru — iki katman:
  1) Boşluk doldurma (slot): birincil esas; boşlukları sonraki kaynaklar KIRPILARAK doldurur.
  2) Alan zenginleştirme (field): aynı programın boş alanını (desc/category) donör kaynaktan doldur.
Birincil her zaman kazanır.
"""
from __future__ import annotations
from datetime import timedelta
from difflib import SequenceMatcher
from typing import List

from models import Programme


def _gaps(progs: List[Programme], far_future=None):
    """Sıralı programlar arasındaki boşlukları döndür.
    Son programdan sonraki boşluğu da döndürür (far_future'a kadar).
    """
    from datetime import timedelta
    progs = sorted(progs, key=lambda p: p.start)
    gaps = []
    cursor = None
    for p in progs:
        if cursor is None:
            cursor = p.stop
            continue
        if p.start > cursor:
            gaps.append((cursor, p.start))
        cursor = max(cursor, p.stop)
    # Son programdan sonraki boşluk
    if cursor is not None:
        end = far_future or (cursor + timedelta(days=14))
        gaps.append((cursor, end))
    return gaps, progs


def merge_sources(source_lists: List[List[Programme]],
                  min_gap_minutes: int = 2,
                  overlap_tol_minutes: int = 5) -> List[Programme]:
    """source_lists öncelik sırasında: [birincil, ikincil, ...]."""
    source_lists = [s for s in source_lists if s]
    if not source_lists:
        return []

    merged = sorted(source_lists[0], key=lambda p: p.start)
    min_gap = timedelta(minutes=min_gap_minutes)

    # 1) BOŞLUK DOLDURMA
    for nxt in source_lists[1:]:
        gaps, merged = _gaps(merged)
        if not merged:
            merged = sorted(nxt, key=lambda p: p.start)
            continue
        for gs, ge in gaps:
            if ge - gs < min_gap:
                continue
            for p in nxt:
                if not p.stop:
                    continue
                if p.stop <= gs or p.start >= ge:
                    continue
                # boşluk sınırlarına KIRP
                clip = Programme(
                    channel_id=p.channel_id,
                    start=max(p.start, gs),
                    stop=min(p.stop, ge),
                    title=p.title, sub_title=p.sub_title,
                    desc=p.desc, category=p.category, source=p.source,
                )
                if clip.stop > clip.start:
                    merged.append(clip)
        merged = sorted(merged, key=lambda p: p.start)

    # 2) ALAN ZENGİNLEŞTİRME
    tol = timedelta(minutes=overlap_tol_minutes)
    for nxt in source_lists[1:]:
        for m in merged:
            if m.desc and m.category:
                continue
            for d in nxt:
                if abs((d.start - m.start).total_seconds()) <= tol.total_seconds():
                    if not m.desc and d.desc:
                        m.desc = d.desc
                    if not m.category and d.category:
                        m.category = d.category
                    if not m.sub_title and d.sub_title:
                        m.sub_title = d.sub_title
                    break
    return merged


def dedup_desc(a: str, b: str, threshold: float = 0.8) -> str:
    """İki açıklama çok benziyorsa tekini döndür, değilse birleştir."""
    if not a:
        return b or ""
    if not b:
        return a
    if SequenceMatcher(None, a, b).ratio() > threshold:
        return a
    return f"{a}\n\n{b}"
