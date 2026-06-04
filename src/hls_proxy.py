"""
HLS Proxy Server — Cloudflare korumalı stream'leri TV'ye iletir.
Domain/CDN bilgisini config/inat_config.json'dan okur (inat_discover.py günceller).

Calistirmak icin:
  python3 src/hls_proxy.py

Playlist'te su formati kullan:
  http://MACBOOK_IP:8888/stream/trt1
"""
from __future__ import annotations
import json
import re
import subprocess
import time
import urllib.parse
from pathlib import Path
from threading import Thread

from flask import Flask, Response, request, abort

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "inat_config.json"
CONFIG_MAX_AGE = 3600  # 1 saat

app = Flask(__name__)

CHANNELS = {
    "trt1":      ("TRT 1",         "tr.trt1"),
    "trtspor":   ("TRT Spor",      "tr.trtspor"),
    "trtspor2":  ("TRT Spor 2",    "tr.trtsporyildiz"),
    "atv":       ("ATV",           "tr.atv"),
    "tv8":       ("TV 8",          "tr.tv8"),
    "tv85":      ("TV 8.5",        "tr.tv85"),
    "as":        ("A Spor",        "tr.aspor"),
    "zirve":     ("BeIN Sports 1", "tr.beinsports1"),
    "b2":        ("BeIN Sports 2", "tr.beinsports2"),
    "b3":        ("BeIN Sports 3", "tr.beinsports3"),
    "b4":        ("BeIN Sports 4", "tr.beinsports4"),
    "bm1":       ("BeIN Max 1",    "tr.beinsportsmax1"),
    "bm2":       ("BeIN Max 2",    "tr.beinsportsmax2"),
    "t2":        ("Tivibu Spor 2", "tr.tivibuspor2"),
    "t3":        ("Tivibu Spor 3", "tr.tivibuspor3"),
    "t4":        ("Tivibu Spor 4", "tr.tivibuspor4"),
    "nbatv":     ("NBA TV",        "tr.nbatv"),
    "eu2":       ("Eurosport 2",   "tr.eurosport2"),
}

# Varsayılan config (discover çalışana kadar)
_config = {
    "domain":   "https://inattv1311.xyz",
    "referer":  "https://inattv1311.xyz/",
    "origin":   "https://inattv1311.xyz",
    "cdn_base": "https://2i4.d72577a9dd0ec71.cfd",
}
_config_loaded_at = 0.0


def load_config():
    global _config, _config_loaded_at
    if CONFIG_PATH.exists():
        try:
            _config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            _config_loaded_at = CONFIG_PATH.stat().st_mtime
            print(f"Config yuklendi: {_config['domain']}")
        except Exception as e:
            print(f"Config okuma hatasi: {e}")


def run_discover():
    """inat_discover.py'yi arka planda calistir."""
    discover_script = Path(__file__).parent / "inat_discover.py"
    print("Discovery basliyor...")
    try:
        subprocess.run(["python3", str(discover_script)], timeout=60, check=False)
        load_config()
    except Exception as e:
        print(f"Discovery hatasi: {e}")


def auto_refresh():
    """Saatlik config yenileme."""
    while True:
        time.sleep(CONFIG_MAX_AGE)
        run_discover()


def get_headers():
    return {
        "referer":    _config["referer"],
        "origin":     _config["origin"],
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "accept":     "*/*",
    }


def fetch(url: str):
    from curl_cffi import requests as cf
    return cf.get(url, headers=get_headers(), impersonate="chrome120", timeout=15)


def rewrite_m3u8(content: str, base_url: str) -> str:
    proxy_base = request.host_url.rstrip("/")
    lines = []
    for line in content.splitlines():
        if line.startswith("http"):
            encoded = urllib.parse.quote(line, safe="")
            lines.append(f"{proxy_base}/segment?url={encoded}")
        elif line and not line.startswith("#"):
            absolute = urllib.parse.urljoin(base_url, line)
            encoded = urllib.parse.quote(absolute, safe="")
            lines.append(f"{proxy_base}/segment?url={encoded}")
        else:
            lines.append(line)
    return "\n".join(lines)


@app.route("/stream/<channel_id>")
def stream(channel_id: str):
    if channel_id not in CHANNELS:
        abort(404)
    m3u8_url = f"{_config['cdn_base']}/{channel_id}/mono.m3u8"
    try:
        resp = fetch(m3u8_url)
    except Exception as e:
        print(f"Stream hatasi {channel_id}: {e}")
        abort(502)
    if resp.status_code != 200:
        print(f"Stream {channel_id}: {resp.status_code} — discovery tetikleniyor")
        Thread(target=run_discover, daemon=True).start()
        abort(resp.status_code)
    content = rewrite_m3u8(resp.text, m3u8_url)
    return Response(content, mimetype="application/vnd.apple.mpegurl",
                    headers={"Access-Control-Allow-Origin": "*"})


@app.route("/segment")
def segment():
    url = request.args.get("url")
    if not url:
        abort(400)
    try:
        resp = fetch(url)
    except Exception as e:
        abort(502)
    ct = resp.headers.get("content-type", "video/MP2T")
    return Response(resp.content, mimetype=ct,
                    headers={"Access-Control-Allow-Origin": "*"})


@app.route("/playlist.m3u")
def playlist():
    host = request.host_url.rstrip("/")
    lines = ["#EXTM3U"]
    for slug, (name, ch_id) in CHANNELS.items():
        lines.append(f'#EXTINF:-1 group-title="Inat TV" tvg-id="{ch_id}",{name}')
        lines.append(f"{host}/stream/{slug}")
    return Response("\n".join(lines), mimetype="audio/x-mpegurl")


@app.route("/status")
def status():
    return {"domain": _config["domain"], "cdn": _config["cdn_base"]}


if __name__ == "__main__":
    import socket

    # Config yükle
    load_config()

    # Config yoksa veya eskiyse discovery çalıştır
    age = time.time() - _config_loaded_at
    if age > CONFIG_MAX_AGE:
        Thread(target=run_discover, daemon=True).start()

    # Saatlik yenileme
    Thread(target=auto_refresh, daemon=True).start()

    ip = socket.gethostbyname(socket.gethostname())
    print(f"\nProxy calisiyor: http://{ip}:8888")
    print(f"Durum:          http://{ip}:8888/status")
    print(f"Playlist:       http://{ip}:8888/playlist.m3u\n")
    for slug, (name, _) in CHANNELS.items():
        print(f"  {name}: http://{ip}:8888/stream/{slug}")

    app.run(host="0.0.0.0", port=8888, debug=False)
