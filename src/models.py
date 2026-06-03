"""Ortak veri modeli. Tüm adaptörler bu biçimde Programme döndürür."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Programme:
    channel_id: str                 # tvg-id (channels.yaml anahtarı)
    start: datetime                 # tz-aware (Europe/Istanbul)
    stop: Optional[datetime] = None # None ise normalize'da türetilir
    title: str = ""
    sub_title: Optional[str] = None
    desc: Optional[str] = None
    category: Optional[str] = None
    year: Optional[int] = None       # yapım yılı (TMDb'den)
    actors: Optional[List[str]] = None  # başroller (TMDb'den)
    source: Optional[str] = None     # hangi adaptörden geldi (debug)

    def key(self) -> tuple:
        """Aynı programı kaynaklar arası eşleştirmek için kaba anahtar."""
        return (self.channel_id, self.start.replace(second=0, microsecond=0))


@dataclass
class Channel:
    id: str            # tvg-id
    name: str
    sources: list = field(default_factory=list)
