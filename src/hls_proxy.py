"""
HLS Proxy Server — Cloudflare korumalı stream'leri TV'ye iletir.
MacBook'ta calistirilir, TV ayni ag uzerinden baglanir.

Calistirmak icin:
  pip install flask curl_cffi
  python src/hls_proxy.py

Playlist'te su formati kullan:
  http://MACBOOK_IP:8888/stream/trt1
  http://MACBOOK_IP:8888/stream/atv
"""
from __future__ import annotations
import re
import urllib.parse
from flask import Flask, Response, request, abort
from curl_cffi import requests as cf

app = Flask(__name__)

CDN_BASE    = "https://2i4.d72577a9dd0ec71.cfd"
REFERER     = "https://inattv1311.xyz/"
ORIGIN      = "https://inattv1311.xyz"

CHANNELS = {
    "trt1":      ("TRT 1",      "tr.trt1"),
    "trtspor":   ("TRT Spor",   "tr.trtspor"),
    "trtspor2":  ("TRT Spor 2", "tr.trtsporyildiz"),
    "atv":       ("ATV",        "tr.atv"),
    "tv8":       ("TV 8",       "tr.tv8"),
    "tv85":      ("TV 8.5",     "tr.tv85"),
    "as":        ("A Spor",     "tr.aspor"),
}

HEADERS = {
    "referer": REFERER,
    "origin":  ORIGIN,
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}

def fetch(url: str) -> cf.Response:
    return cf.get(url, headers=HEADERS, impersonate="chrome120", timeout=15)


def rewrite_m3u8(content: str, channel_id: str, base_url: str) -> str:
    """Segment URL'lerini proxy uzerinden gecir."""
    proxy_base = request.host_url.rstrip("/")
    lines = []
    for line in content.splitlines():
        if line.startswith("http"):
            encoded = urllib.parse.quote(line, safe="")
            lines.append(f"{proxy_base}/segment?url={encoded}")
        elif line and not line.startswith("#") and not line.startswith("http"):
            # Relative URL
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
    m3u8_url = f"{CDN_BASE}/{channel_id}/mono.m3u8"
    resp = fetch(m3u8_url)
    if resp.status_code != 200:
        abort(resp.status_code)
    content = rewrite_m3u8(resp.text, channel_id, m3u8_url)
    return Response(content, mimetype="application/vnd.apple.mpegurl",
                    headers={"Access-Control-Allow-Origin": "*"})


@app.route("/segment")
def segment():
    url = request.args.get("url")
    if not url:
        abort(400)
    resp = fetch(url)
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


if __name__ == "__main__":
    import socket
    ip = socket.gethostbyname(socket.gethostname())
    print(f"\nProxy calisiyor: http://{ip}:8888")
    print(f"Playlist URL:   http://{ip}:8888/playlist.m3u\n")
    for slug, (name, _) in CHANNELS.items():
        print(f"  {name}: http://{ip}:8888/stream/{slug}")
    app.run(host="0.0.0.0", port=8888, debug=False)
