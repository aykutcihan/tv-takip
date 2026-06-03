"""
TMDb film zenginleştirme.
- Açıklama: skip_desc_sources'ta olan kaynaklarda (ör. tvplus) DOKUNMAZ.
  Diğer kaynaklar için açıklama zayıfsa TMDb'den çeker.
- Yıl & başrol: TÜM film programları için eksikse doldurur (kaynak farketmez).
Eşleşme düşük güvenliyse yine DOKUNMAZ (yanlış veri koymaktansa boş bırak).
Sonuçlar diskte cache'lenir -> deterministik çıktı + API'yi yormama.
"""
from __future__ import annotations
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

import requests

from models import Programme


class TMDbEnricher:
    def __init__(self, cfg: dict):
        self.enabled = cfg.get("enabled", False)
        self.key = os.environ.get(cfg.get("api_key_env", "TMDB_API_KEY"), "")
        self.lang = cfg.get("language", "tr-TR")
        self.cache_path = Path(cfg.get("cache_path", "cache/tmdb.json"))
        self.film_cats = {c.lower() for c in cfg.get("film_categories", ["film"])}
        self.min_len = cfg.get("min_desc_len", 40)
        self.skip_desc_sources = set(cfg.get("skip_desc_sources", []))
        self.max_actors = cfg.get("max_actors", 3)
        self._cache: Dict[str, dict] = self._load_cache()
        if self.enabled and not self.key:
            print("[tmdb] uyarı: API anahtarı yok, zenginleştirme atlanıyor.")
            self.enabled = False

    def _load_cache(self) -> Dict[str, dict]:
        try:
            raw = json.loads(self.cache_path.read_text("utf-8"))
            # Eski format: {key: "string"} → yeni format: {key: {desc, year, actors}}
            migrated = {}
            for k, v in raw.items():
                if isinstance(v, str):
                    migrated[k] = {"desc": v or None, "year": None, "actors": []}
                else:
                    migrated[k] = v
            return migrated
        except Exception:
            return {}

    def save(self):
        if not self.enabled:
            return
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(
            json.dumps(self._cache, ensure_ascii=False, indent=2, sort_keys=True),
            "utf-8")

    def _is_film(self, p: Programme) -> bool:
        cat = (p.category or "").lower()
        return any(fc in cat for fc in self.film_cats)

    def _needs_desc(self, p: Programme) -> bool:
        if p.source in self.skip_desc_sources:
            return False
        return not p.desc or len(p.desc) < self.min_len

    def _needs_meta(self, p: Programme) -> bool:
        return p.year is None or not p.actors

    def _lookup(self, title: str) -> dict:
        ck = f"{title}|"
        if ck in self._cache:
            return self._cache[ck]

        result: dict = {"desc": None, "year": None, "actors": []}
        try:
            r = requests.get(
                "https://api.themoviedb.org/3/search/movie",
                params={"api_key": self.key, "query": title, "language": self.lang},
                timeout=15)
            r.raise_for_status()
            results = r.json().get("results", [])
            if results:
                movie = results[0]
                movie_id = movie.get("id")
                overview = (movie.get("overview") or "").strip()
                result["desc"] = overview or None

                date_str = movie.get("release_date") or ""
                if len(date_str) >= 4:
                    result["year"] = int(date_str[:4])

                if movie_id and self.max_actors > 0:
                    cr = requests.get(
                        f"https://api.themoviedb.org/3/movie/{movie_id}/credits",
                        params={"api_key": self.key, "language": self.lang},
                        timeout=15)
                    cr.raise_for_status()
                    cast = cr.json().get("cast", [])
                    result["actors"] = [m["name"] for m in cast[:self.max_actors]]
        except Exception as e:
            print(f"[tmdb] hata ({title}): {e}")

        self._cache[ck] = result
        return result

    def enrich(self, programmes):
        if not self.enabled:
            return
        for p in programmes:
            if not self._is_film(p):
                continue
            needs_desc = self._needs_desc(p)
            needs_meta = self._needs_meta(p)
            if not needs_desc and not needs_meta:
                continue

            title = re.sub(r"\s*\(.*?\)\s*$", "", (p.title or "")).strip()
            if not title:
                continue

            data = self._lookup(title)
            if needs_desc and data.get("desc"):
                p.desc = data["desc"]
            if p.year is None and data.get("year"):
                p.year = data["year"]
            if not p.actors and data.get("actors"):
                p.actors = data["actors"]
