"""Kaynaksız kanallar için sentetik bloklar (2 saatlik, rolling N gün)."""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import List

from models import Programme
from normalize import ist

TEXT = "Kaynaktaki teknik sorun nedeniyle yayın akışı bilgisi geçici olarak alınamıyor"


def placeholder_programmes(channel_id: str, days: int = 7,
                           block_hours: int = 2) -> List[Programme]:
    now = ist(datetime.now()).replace(minute=0, second=0, microsecond=0)
    # gün başına hizala
    start = now.replace(hour=(now.hour // block_hours) * block_hours)
    out: List[Programme] = []
    blocks = (24 // block_hours) * days
    cur = start
    for _ in range(blocks):
        nxt = cur + timedelta(hours=block_hours)
        out.append(Programme(
            channel_id=channel_id, start=cur, stop=nxt,
            title=TEXT, source="placeholder",
        ))
        cur = nxt
    return out
