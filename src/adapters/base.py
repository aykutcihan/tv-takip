"""Adaptör portu: her site için bir adaptör. Kanal başına değil, SİTE başına."""
from __future__ import annotations
import time
import requests
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from models import Programme

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)


class BaseAdapter(ABC):
    prefix: str = ""          # 'tvplus', 'tivibu', ...
    base_url: str = ""

    def __init__(self, session: requests.Session | None = None, delay: float = 0.2):
        self.s = session or requests.Session()
        self.s.headers.update({
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        })
        self.delay = delay

    def _get(self, url: str, **kw) -> requests.Response:
        time.sleep(self.delay)  # kaynağı yormamak için nazik gecikme
        r = self.s.get(url, timeout=20, **kw)
        r.raise_for_status()
        return r

    @abstractmethod
    def fetch(self, source_id: str, channel_id: str) -> List[Programme]:
        """source_id (ör. 'star-tv-hd--89') için programları döndür."""
        ...
