"""
staticschedule — Sabit haftalık/günlük yayın akışı döngüsü.

Her hafta/gün aynı programı tekrar eden kanallar için kullanılır.

Format iki türlü olabilir:
  - Haftalık (farklı günler): "tr.kanal": {"tz": TZ, "days": {0: [...], 1: [...], ...}}
  - Günlük (her gün aynı): "tr.kanal": {"tz": TZ, "daily": [...]}

Tuple: (saat, dakika, başlık) veya (saat, dakika, başlık, açıklama)

source_id = channel_id (channels.yaml'da kanalın tvg-id'si ile eşleşir)
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

from dateutil import tz

from adapters.base import BaseAdapter
from models import Programme
from normalize import ist

DE_TZ  = tz.tzoffset("CET", 3600)    # Sabit UTC+1 (Kanal Avrupa yayın saati)
IST_TZ = tz.gettz("Europe/Istanbul")

# Gün numarası: 0=Pazartesi, 1=Salı, ..., 6=Pazar
SCHEDULES: Dict[str, Dict] = {

    # ── KANAL 6 — Haftalık yayın akışı ───────────────────────────
    "tr.kanal6": {
        "tz": IST_TZ,
        "days": {
            0: [  # Pazartesi
                ( 7, 0, "Güneş Doğarken"), ( 8,30, "Çizgi Film"),
                ( 9, 0, "Mutlu Yaşam İçin"), (10, 0, "Bir Başka Sabah"),
                (12, 0, "Öğle Haberi"), (12,30, "Burada Engelsizsin"),
                (13,30, "İş'te Moda"), (14,30, "İzleyicinin Seyir Defteri"),
                (15,30, "Dikkat Sağlık"), (17, 0, "İş'te Kariyer"),
                (18, 0, "SIT-COM Captain"), (19, 0, "Ana Haber"),
                (20, 0, "Kimde Kaldı?"), (21,30, "Faktör"),
                (23, 0, "Gece Sineması"), ( 1, 0, "Bi' Başka Ara"),
                ( 1,30, "Son Çıkış"), ( 3, 0, "Konser"),
                ( 5, 0, "Belgesel"), ( 6, 0, "Müzik"),
            ],
            1: [  # Salı
                ( 7, 0, "Güneş Doğarken"), ( 8,30, "Çizgi Film"),
                ( 9, 0, "Mutlu Yaşam İçin"), (10, 0, "Bir Başka Sabah"),
                (12, 0, "Öğle Haberi"), (12,30, "Burada Engelsizsin"),
                (13,30, "Notalara Yolculuk"), (14,30, "1 Kadın 4 Konuk"),
                (15,30, "Dikkat Sağlık"), (17, 0, "İş'te Kariyer"),
                (18, 0, "SIT-COM Captain"), (19, 0, "Ana Haber"),
                (20, 0, "Kimde Kaldı?"), (21,30, "Önce İletişim"),
                (23, 0, "Gece Sineması"), ( 1, 0, "Bi' Başka Ara"),
                ( 1,30, "Son Çıkış"), ( 3, 0, "Konser"),
                ( 5, 0, "Belgesel"), ( 6, 0, "Müzik"),
            ],
            2: [  # Çarşamba
                ( 7, 0, "Güneş Doğarken"), ( 8,30, "Çizgi Film"),
                ( 9, 0, "Mutlu Yaşam İçin"), (10, 0, "Bir Başka Sabah"),
                (12, 0, "Öğle Haberi"), (12,30, "Burada Engelsizsin"),
                (13,30, "İş'te Moda"), (14,30, "1 Kadın 4 Konuk"),
                (15,30, "Dikkat Sağlık"), (17, 0, "X'in Dükkânı"),
                (18, 0, "SIT-COM Captain"), (19, 0, "Ana Haber"),
                (20, 0, "Kimde Kaldı?"), (21,30, "Tebdil-i Mekan"),
                (23, 0, "Gece Sineması"), ( 1, 0, "Bi' Başka Ara"),
                ( 1,30, "Son Çıkış"), ( 3, 0, "Konser"),
                ( 5, 0, "Belgesel"), ( 6, 0, "Müzik"),
            ],
            3: [  # Perşembe
                ( 7, 0, "Güneş Doğarken"), ( 8,30, "Çizgi Film"),
                ( 9, 0, "Mutlu Yaşam İçin"), (10, 0, "Bir Başka Sabah"),
                (12, 0, "Öğle Haberi"), (12,30, "Burada Engelsizsin"),
                (13,30, "Notalara Yolculuk"), (14,30, "1 Kadın 4 Konuk"),
                (15,30, "Dikkat Sağlık"), (17, 0, "X'in Dükkânı"),
                (18, 0, "SIT-COM Captain"), (19, 0, "Ana Haber"),
                (20, 0, "Kimde Kaldı?"), (21,30, "Avrupa Durağı"),
                (23, 0, "Gece Sineması"), ( 1, 0, "Bi' Başka Ara"),
                ( 1,30, "Son Çıkış"), ( 3, 0, "Konser"),
                ( 5, 0, "Belgesel"), ( 6, 0, "Müzik"),
            ],
            4: [  # Cuma
                ( 7, 0, "Güneş Doğarken"), ( 8,30, "Çizgi Film"),
                ( 9, 0, "Mutlu Yaşam İçin"), (10, 0, "Bir Başka Sabah"),
                (12, 0, "Öğle Haberi"), (12,30, "Burada Engelsizsin"),
                (13,30, "İş'te Moda"), (14,30, "İzleyicinin Seyir Defteri"),
                (15,30, "Dikkat Sağlık"), (17, 0, "X'in Dükkânı"),
                (18, 0, "Dizi Pati and Pati"), (19, 0, "Ana Haber"),
                (20, 0, "Kimde Kaldı?"), (21,30, "Asansör"),
                (23, 0, "Gece Sineması"), ( 1, 0, "Bi' Başka Ara"),
                ( 1,30, "Son Çıkış"), ( 3, 0, "Konser"),
                ( 5, 0, "Belgesel"), ( 6, 0, "Müzik"),
            ],
            5: [  # Cumartesi
                ( 7, 0, "Ana Sayfa"), ( 8,30, "Çizgi Film"),
                ( 9, 0, "12'den Vuranlar"), (10, 0, "Pembe Yaşamlar"),
                (12, 0, "Öğle Haberi"), (12,30, "Turizm 'E'"),
                (13,30, "Star Pabuç"), (14,30, "Engelsiz Mekanlar"),
                (15,30, "Ekonomik Yaşam"), (17, 0, "Bi' Başka Ara"),
                (18, 0, "Hayatımızı Değiştirenler"),
                (19, 0, "X ile Hafta Sonu Haberleri"),
                (20, 0, "Tüm Engellere Rağmen Ben De Yapabilirim"),
                (23, 0, "Gece Sineması"), ( 1, 0, "Bi' Başka Ara"),
                ( 1,30, "Son Çıkış"), ( 3, 0, "Konser"),
                ( 5, 0, "Belgesel"), ( 6, 0, "Müzik"),
            ],
            6: [  # Pazar
                ( 7, 0, "Belgesel"), ( 8,30, "Çizgi Film"),
                ( 9, 0, "12'den Vuranlar"), (10, 0, "Pembe Yaşamlar"),
                (12, 0, "Öğle Haberi"), (12,30, "Turizm 'E'"),
                (13,30, "Star Pabuç"), (14,30, "Engelsiz Mekanlar"),
                (15,30, "Ekonomik Yaşam"), (17, 0, "Bi' Başka Ara"),
                (18, 0, "Hayatımızı Değiştirenler"),
                (19, 0, "X ile Hafta Sonu Haberleri"),
                (20, 0, "Tüm Engellere Rağmen Ben De Yapabilirim"),
                (23, 0, "Gece Sineması"), ( 1, 0, "Bi' Başka Ara"),
                ( 1,30, "Son Çıkış"), ( 3, 0, "Konser"),
                ( 5, 0, "Belgesel"), ( 6, 0, "Müzik"),
            ],
        },
    },


    # ── POWER DANCE — 2 saatlik elektronik/dans döngüsü ──────────
    "tr.powerdance": {
        "tz": IST_TZ,
        "daily": [
            ( 0, 0, "Müzik Yayını", "Dance, elektronik ve EDM müzik yayını"),
            ( 2, 0, "Müzik Yayını", "Dance, elektronik ve EDM müzik yayını"),
            ( 4, 0, "Müzik Yayını", "Dance, elektronik ve EDM müzik yayını"),
            ( 6, 0, "Müzik Yayını", "Dance, elektronik ve EDM müzik yayını"),
            ( 8, 0, "Müzik Yayını", "Dance, elektronik ve EDM müzik yayını"),
            (10, 0, "Müzik Yayını", "Dance, elektronik ve EDM müzik yayını"),
            (12, 0, "Müzik Yayını", "Dance, elektronik ve EDM müzik yayını"),
            (14, 0, "Müzik Yayını", "Dance, elektronik ve EDM müzik yayını"),
            (16, 0, "Müzik Yayını", "Dance, elektronik ve EDM müzik yayını"),
            (18, 0, "Müzik Yayını", "Dance, elektronik ve EDM müzik yayını"),
            (20, 0, "Müzik Yayını", "Dance, elektronik ve EDM müzik yayını"),
            (22, 0, "Müzik Yayını", "Dance, elektronik ve EDM müzik yayını"),
        ],
    },
    # ── POWER LOVE — 2 saatlik romantik müzik döngüsü ────────────
    "tr.powerlove": {
        "tz": IST_TZ,
        "daily": [
            ( 0, 0, "Müzik Yayını", "Aşk şarkıları ve romantik Türkçe müzik yayını"),
            ( 2, 0, "Müzik Yayını", "Aşk şarkıları ve romantik Türkçe müzik yayını"),
            ( 4, 0, "Müzik Yayını", "Aşk şarkıları ve romantik Türkçe müzik yayını"),
            ( 6, 0, "Müzik Yayını", "Aşk şarkıları ve romantik Türkçe müzik yayını"),
            ( 8, 0, "Müzik Yayını", "Aşk şarkıları ve romantik Türkçe müzik yayını"),
            (10, 0, "Müzik Yayını", "Aşk şarkıları ve romantik Türkçe müzik yayını"),
            (12, 0, "Müzik Yayını", "Aşk şarkıları ve romantik Türkçe müzik yayını"),
            (14, 0, "Müzik Yayını", "Aşk şarkıları ve romantik Türkçe müzik yayını"),
            (16, 0, "Müzik Yayını", "Aşk şarkıları ve romantik Türkçe müzik yayını"),
            (18, 0, "Müzik Yayını", "Aşk şarkıları ve romantik Türkçe müzik yayını"),
            (20, 0, "Müzik Yayını", "Aşk şarkıları ve romantik Türkçe müzik yayını"),
            (22, 0, "Müzik Yayını", "Aşk şarkıları ve romantik Türkçe müzik yayını"),
        ],
    },
    # ── POWERTURK SLOW — 2 saatlik yavaş tempo döngüsü ──────────
    "tr.powerturkslow": {
        "tz": IST_TZ,
        "daily": [
            ( 0, 0, "Müzik Yayını", "Yavaş tempo, duygusal Türkçe müzik yayını"),
            ( 2, 0, "Müzik Yayını", "Yavaş tempo, duygusal Türkçe müzik yayını"),
            ( 4, 0, "Müzik Yayını", "Yavaş tempo, duygusal Türkçe müzik yayını"),
            ( 6, 0, "Müzik Yayını", "Yavaş tempo, duygusal Türkçe müzik yayını"),
            ( 8, 0, "Müzik Yayını", "Yavaş tempo, duygusal Türkçe müzik yayını"),
            (10, 0, "Müzik Yayını", "Yavaş tempo, duygusal Türkçe müzik yayını"),
            (12, 0, "Müzik Yayını", "Yavaş tempo, duygusal Türkçe müzik yayını"),
            (14, 0, "Müzik Yayını", "Yavaş tempo, duygusal Türkçe müzik yayını"),
            (16, 0, "Müzik Yayını", "Yavaş tempo, duygusal Türkçe müzik yayını"),
            (18, 0, "Müzik Yayını", "Yavaş tempo, duygusal Türkçe müzik yayını"),
            (20, 0, "Müzik Yayını", "Yavaş tempo, duygusal Türkçe müzik yayını"),
            (22, 0, "Müzik Yayını", "Yavaş tempo, duygusal Türkçe müzik yayını"),
        ],
    },
    # ── POWERTURK AKUSTİK — 2 saatlik akustik döngüsü ───────────
    "tr.powerturkakustik": {
        "tz": IST_TZ,
        "daily": [
            ( 0, 0, "Müzik Yayını", "Akustik Türkçe müzik ve unplugged performanslar"),
            ( 2, 0, "Müzik Yayını", "Akustik Türkçe müzik ve unplugged performanslar"),
            ( 4, 0, "Müzik Yayını", "Akustik Türkçe müzik ve unplugged performanslar"),
            ( 6, 0, "Müzik Yayını", "Akustik Türkçe müzik ve unplugged performanslar"),
            ( 8, 0, "Müzik Yayını", "Akustik Türkçe müzik ve unplugged performanslar"),
            (10, 0, "Müzik Yayını", "Akustik Türkçe müzik ve unplugged performanslar"),
            (12, 0, "Müzik Yayını", "Akustik Türkçe müzik ve unplugged performanslar"),
            (14, 0, "Müzik Yayını", "Akustik Türkçe müzik ve unplugged performanslar"),
            (16, 0, "Müzik Yayını", "Akustik Türkçe müzik ve unplugged performanslar"),
            (18, 0, "Müzik Yayını", "Akustik Türkçe müzik ve unplugged performanslar"),
            (20, 0, "Müzik Yayını", "Akustik Türkçe müzik ve unplugged performanslar"),
            (22, 0, "Müzik Yayını", "Akustik Türkçe müzik ve unplugged performanslar"),
        ],
    },
    # ── POWERTURK EN İYİLER — 2 saatlik döngü ───────────────────
    "tr.powerturkeniyiler": {
        "tz": IST_TZ,
        "daily": [
            ( 0, 0, "Müzik Yayını", "En iyi Türkçe pop hitleri non-stop yayın"),
            ( 2, 0, "Müzik Yayını", "En iyi Türkçe pop hitleri non-stop yayın"),
            ( 4, 0, "Müzik Yayını", "En iyi Türkçe pop hitleri non-stop yayın"),
            ( 6, 0, "Müzik Yayını", "En iyi Türkçe pop hitleri non-stop yayın"),
            ( 8, 0, "Müzik Yayını", "En iyi Türkçe pop hitleri non-stop yayın"),
            (10, 0, "Müzik Yayını", "En iyi Türkçe pop hitleri non-stop yayın"),
            (12, 0, "Müzik Yayını", "En iyi Türkçe pop hitleri non-stop yayın"),
            (14, 0, "Müzik Yayını", "En iyi Türkçe pop hitleri non-stop yayın"),
            (16, 0, "Müzik Yayını", "En iyi Türkçe pop hitleri non-stop yayın"),
            (18, 0, "Müzik Yayını", "En iyi Türkçe pop hitleri non-stop yayın"),
            (20, 0, "Müzik Yayını", "En iyi Türkçe pop hitleri non-stop yayın"),
            (22, 0, "Müzik Yayını", "En iyi Türkçe pop hitleri non-stop yayın"),
        ],
    },
    # ── POWERTURK TAPTAZE — 2 saatlik yeni müzik döngüsü ────────
    "tr.powerturktaptaze": {
        "tz": IST_TZ,
        "daily": [
            ( 0, 0, "Müzik Yayını", "Güncel ve yeni Türkçe pop müzik yayını"),
            ( 2, 0, "Müzik Yayını", "Güncel ve yeni Türkçe pop müzik yayını"),
            ( 4, 0, "Müzik Yayını", "Güncel ve yeni Türkçe pop müzik yayını"),
            ( 6, 0, "Müzik Yayını", "Güncel ve yeni Türkçe pop müzik yayını"),
            ( 8, 0, "Müzik Yayını", "Güncel ve yeni Türkçe pop müzik yayını"),
            (10, 0, "Müzik Yayını", "Güncel ve yeni Türkçe pop müzik yayını"),
            (12, 0, "Müzik Yayını", "Güncel ve yeni Türkçe pop müzik yayını"),
            (14, 0, "Müzik Yayını", "Güncel ve yeni Türkçe pop müzik yayını"),
            (16, 0, "Müzik Yayını", "Güncel ve yeni Türkçe pop müzik yayını"),
            (18, 0, "Müzik Yayını", "Güncel ve yeni Türkçe pop müzik yayını"),
            (20, 0, "Müzik Yayını", "Güncel ve yeni Türkçe pop müzik yayını"),
            (22, 0, "Müzik Yayını", "Güncel ve yeni Türkçe pop müzik yayını"),
        ],
    },
    # ── POWER PLUS — 2 saatlik uluslararası pop döngüsü ─────────
    "tr.powerplus": {
        "tz": IST_TZ,
        "daily": [
            ( 0, 0, "Müzik Yayını", "Uluslararası pop hitleri ve İngilizce müzik yayını"),
            ( 2, 0, "Müzik Yayını", "Uluslararası pop hitleri ve İngilizce müzik yayını"),
            ( 4, 0, "Müzik Yayını", "Uluslararası pop hitleri ve İngilizce müzik yayını"),
            ( 6, 0, "Müzik Yayını", "Uluslararası pop hitleri ve İngilizce müzik yayını"),
            ( 8, 0, "Müzik Yayını", "Uluslararası pop hitleri ve İngilizce müzik yayını"),
            (10, 0, "Müzik Yayını", "Uluslararası pop hitleri ve İngilizce müzik yayını"),
            (12, 0, "Müzik Yayını", "Uluslararası pop hitleri ve İngilizce müzik yayını"),
            (14, 0, "Müzik Yayını", "Uluslararası pop hitleri ve İngilizce müzik yayını"),
            (16, 0, "Müzik Yayını", "Uluslararası pop hitleri ve İngilizce müzik yayını"),
            (18, 0, "Müzik Yayını", "Uluslararası pop hitleri ve İngilizce müzik yayını"),
            (20, 0, "Müzik Yayını", "Uluslararası pop hitleri ve İngilizce müzik yayını"),
            (22, 0, "Müzik Yayını", "Uluslararası pop hitleri ve İngilizce müzik yayını"),
        ],
    },

    # ── SLOW KARADENİZ — 2 saatlik döngü ────────────────────────
    "tr.slowkaradeniz": {
        "tz": IST_TZ,
        "daily": [(h, 0, "Karadeniz Yöresi Şarkıları", "Karadeniz yöresi türküleri ve horon müziği yayını") for h in range(0, 24, 2)],
    },

    # ── MÜZİK KANALLARI — 2 saatlik döngüler ─────────────────────
    "tr.toppop": {
        "tz": IST_TZ,
        "daily": [(h, 0, "Müzik Yayını", "Pop müzik video yayını") for h in range(0, 24, 2)],
    },
    "tr.finest": {
        "tz": IST_TZ,
        "daily": [(h, 0, "Türkçe Pop Yayını", "Türkçe pop müzik video yayını") for h in range(0, 24, 2)],
    },
    "tr.guclutv": {
        "tz": IST_TZ,
        "daily": [(h, 0, "Özgün Müzik Yayını", "Özgün ve yöresel Türk müziği yayını") for h in range(0, 24, 2)],
    },
    "tr.dostmuzik": {
        "tz": IST_TZ,
        "daily": [(h, 0, "Halk Müziği Yayını", "Türk halk müziği ve türkü yayını") for h in range(0, 24, 2)],
    },
    "tr.gencsms": {
        "tz": IST_TZ,
        "daily": [(h, 0, "Müzik Yayını", "Genç dinleyicilere yönelik müzik video yayını") for h in range(0, 24, 2)],
    },
    "tr.armatv": {
        "tz": IST_TZ,
        "daily": [(h, 0, "Arabesk Müzik Yayını", "Arabesk ve Türk sanat müziği video yayını") for h in range(0, 24, 2)],
    },
    "tr.silatv": {
        "tz": IST_TZ,
        "daily": [(h, 0, "Arabesk Müzik Yayını", "Arabesk ve duygusal Türk müziği yayını") for h in range(0, 24, 2)],
    },
    "tr.damartv": {
        "tz": IST_TZ,
        "daily": [(h, 0, "Damar Arabesk Yayını", "Damar arabesk müzik video yayını") for h in range(0, 24, 2)],
    },
    "tr.ezotv": {
        "tz": IST_TZ,
        "daily": [(h, 0, "Halk Müziği Yayını", "Türk halk müziği ve yöresel türküler yayını") for h in range(0, 24, 2)],
    },
    "tr.ezgitv": {
        "tz": IST_TZ,
        "daily": [(h, 0, "Özgün Müzik Yayını", "Özgün ve kültürel Türk müziği yayını") for h in range(0, 24, 2)],
    },

    # ── CHILL TV — 2 saatlik sakinleştirici müzik döngüsü ────────
    "tr.chilltv": {
        "tz": IST_TZ,
        "daily": [
            ( 0, 0, "Lounge Müzik Yayını", "Sakinleştirici, lounge ve ambient müzik yayını"),
            ( 2, 0, "Lounge Müzik Yayını", "Sakinleştirici, lounge ve ambient müzik yayını"),
            ( 4, 0, "Lounge Müzik Yayını", "Sakinleştirici, lounge ve ambient müzik yayını"),
            ( 6, 0, "Lounge Müzik Yayını", "Sakinleştirici, lounge ve ambient müzik yayını"),
            ( 8, 0, "Lounge Müzik Yayını", "Sakinleştirici, lounge ve ambient müzik yayını"),
            (10, 0, "Lounge Müzik Yayını", "Sakinleştirici, lounge ve ambient müzik yayını"),
            (12, 0, "Lounge Müzik Yayını", "Sakinleştirici, lounge ve ambient müzik yayını"),
            (14, 0, "Lounge Müzik Yayını", "Sakinleştirici, lounge ve ambient müzik yayını"),
            (16, 0, "Lounge Müzik Yayını", "Sakinleştirici, lounge ve ambient müzik yayını"),
            (18, 0, "Lounge Müzik Yayını", "Sakinleştirici, lounge ve ambient müzik yayını"),
            (20, 0, "Lounge Müzik Yayını", "Sakinleştirici, lounge ve ambient müzik yayını"),
            (22, 0, "Lounge Müzik Yayını", "Sakinleştirici, lounge ve ambient müzik yayını"),
        ],
    },

    # ── TEMPO TV ──────────────────────────────────────────────────
    "tr.tempotv": {
        "tz": IST_TZ,
        "daily": [
            ( 0, 0, "Klip Saati",    "Türkçe pop ve arabesk müzik klipleri"),
            ( 2, 0, "Klip Saati",    "Türkçe pop ve arabesk müzik klipleri"),
            ( 4, 0, "Klip Saati",    "Türkçe pop ve arabesk müzik klipleri"),
            ( 6, 0, "Klip Saati",    "Türkçe pop ve arabesk müzik klipleri"),
            ( 8, 0, "Klip Saati",    "Türkçe pop ve arabesk müzik klipleri"),
            (10, 0, "Klip Saati",    "Türkçe pop ve arabesk müzik klipleri"),
            (12, 0, "Klip Saati",    "Türkçe pop ve arabesk müzik klipleri"),
            (14, 0, "Klip Saati",    "Türkçe pop ve arabesk müzik klipleri"),
            (16, 0, "Klip Saati",    "Türkçe pop ve arabesk müzik klipleri"),
            (19, 0, "Müzik Programı","Canlı müzik yayını ve müzik programları"),
            (21, 0, "Müzik Programı","Canlı müzik yayını ve müzik programları"),
            (23, 0, "Müzik Programı","Canlı müzik yayını ve müzik programları"),
        ],
    },

    # ── KRAL TV KANALLARI ─────────────────────────────────────────
    "tr.kraltv": {
        "tz": IST_TZ,
        "daily": [
            ( 0, 0, "Kral TV Yayını", "Türkü, halk müziği ve Türk sanat müziği video yayını"),
            ( 2, 0, "Kral TV Yayını", "Türkü, halk müziği ve Türk sanat müziği video yayını"),
            ( 4, 0, "Kral TV Yayını", "Türkü, halk müziği ve Türk sanat müziği video yayını"),
            ( 6, 0, "Kral TV Yayını", "Türkü, halk müziği ve Türk sanat müziği video yayını"),
            ( 8, 0, "Kral TV Yayını", "Türkü, halk müziği ve Türk sanat müziği video yayını"),
            (10, 0, "Kral TV Yayını", "Türkü, halk müziği ve Türk sanat müziği video yayını"),
            (12, 0, "Kral TV Yayını", "Türkü, halk müziği ve Türk sanat müziği video yayını"),
            (14, 0, "Kral TV Yayını", "Türkü, halk müziği ve Türk sanat müziği video yayını"),
            (16, 0, "Kral TV Yayını", "Türkü, halk müziği ve Türk sanat müziği video yayını"),
            (18, 0, "Kral TV Yayını", "Türkü, halk müziği ve Türk sanat müziği video yayını"),
            (20, 0, "Kral TV Yayını", "Türkü, halk müziği ve Türk sanat müziği video yayını"),
            (22, 0, "Kral TV Yayını", "Türkü, halk müziği ve Türk sanat müziği video yayını"),
        ],
    },
    "tr.kralpoptv": {
        "tz": IST_TZ,
        "daily": [
            ( 0, 0, "Kral Pop TV Yayını", "Türkçe pop müzik video kanalı yayını"),
            ( 2, 0, "Kral Pop TV Yayını", "Türkçe pop müzik video kanalı yayını"),
            ( 4, 0, "Kral Pop TV Yayını", "Türkçe pop müzik video kanalı yayını"),
            ( 6, 0, "Kral Pop TV Yayını", "Türkçe pop müzik video kanalı yayını"),
            ( 8, 0, "Kral Pop TV Yayını", "Türkçe pop müzik video kanalı yayını"),
            (10, 0, "Kral Pop TV Yayını", "Türkçe pop müzik video kanalı yayını"),
            (12, 0, "Kral Pop TV Yayını", "Türkçe pop müzik video kanalı yayını"),
            (14, 0, "Kral Pop TV Yayını", "Türkçe pop müzik video kanalı yayını"),
            (16, 0, "Kral Pop TV Yayını", "Türkçe pop müzik video kanalı yayını"),
            (18, 0, "Kral Pop TV Yayını", "Türkçe pop müzik video kanalı yayını"),
            (20, 0, "Kral Pop TV Yayını", "Türkçe pop müzik video kanalı yayını"),
            (22, 0, "Kral Pop TV Yayını", "Türkçe pop müzik video kanalı yayını"),
        ],
    },

    # ── NR1 / NUMBER1 KANALLARI ──────────────────────────────────
    "tr.nr1rap": {
        "tz": IST_TZ,
        "daily": [
            ( 0, 0, "NR1 Rap Yayını", "Türkçe rap, hip-hop ve trap müzik yayını"),
            ( 2, 0, "NR1 Rap Yayını", "Türkçe rap, hip-hop ve trap müzik yayını"),
            ( 4, 0, "NR1 Rap Yayını", "Türkçe rap, hip-hop ve trap müzik yayını"),
            ( 6, 0, "NR1 Rap Yayını", "Türkçe rap, hip-hop ve trap müzik yayını"),
            ( 8, 0, "NR1 Rap Yayını", "Türkçe rap, hip-hop ve trap müzik yayını"),
            (10, 0, "NR1 Rap Yayını", "Türkçe rap, hip-hop ve trap müzik yayını"),
            (12, 0, "NR1 Rap Yayını", "Türkçe rap, hip-hop ve trap müzik yayını"),
            (14, 0, "NR1 Rap Yayını", "Türkçe rap, hip-hop ve trap müzik yayını"),
            (16, 0, "NR1 Rap Yayını", "Türkçe rap, hip-hop ve trap müzik yayını"),
            (18, 0, "NR1 Rap Yayını", "Türkçe rap, hip-hop ve trap müzik yayını"),
            (20, 0, "NR1 Rap Yayını", "Türkçe rap, hip-hop ve trap müzik yayını"),
            (22, 0, "NR1 Rap Yayını", "Türkçe rap, hip-hop ve trap müzik yayını"),
        ],
    },
    "tr.number1tv": {
        "tz": IST_TZ,
        "daily": [
            ( 0, 0, "Müzik Yayını", "Yabancı pop müzik video yayını"),
            ( 2, 0, "Müzik Yayını", "Yabancı pop müzik video yayını"),
            ( 4, 0, "Müzik Yayını", "Yabancı pop müzik video yayını"),
            ( 6, 0, "Müzik Yayını", "Yabancı pop müzik video yayını"),
            ( 8, 0, "Müzik Yayını", "Yabancı pop müzik video yayını"),
            (10, 0, "Müzik Yayını", "Yabancı pop müzik video yayını"),
            (12, 0, "Müzik Yayını", "Yabancı pop müzik video yayını"),
            (14, 0, "Müzik Yayını", "Yabancı pop müzik video yayını"),
            (16, 0, "Müzik Yayını", "Yabancı pop müzik video yayını"),
            (18, 0, "Müzik Yayını", "Yabancı pop müzik video yayını"),
            (20, 0, "Müzik Yayını", "Yabancı pop müzik video yayını"),
            (22, 0, "Müzik Yayını", "Yabancı pop müzik video yayını"),
        ],
    },
    "tr.number1turk": {
        "tz": IST_TZ,
        "daily": [
            ( 0, 0, "Number1 Türk Yayını", "Türkçe pop ve arabesk müzik video yayını"),
            ( 2, 0, "Number1 Türk Yayını", "Türkçe pop ve arabesk müzik video yayını"),
            ( 4, 0, "Number1 Türk Yayını", "Türkçe pop ve arabesk müzik video yayını"),
            ( 6, 0, "Number1 Türk Yayını", "Türkçe pop ve arabesk müzik video yayını"),
            ( 8, 0, "Number1 Türk Yayını", "Türkçe pop ve arabesk müzik video yayını"),
            (10, 0, "Number1 Türk Yayını", "Türkçe pop ve arabesk müzik video yayını"),
            (12, 0, "Number1 Türk Yayını", "Türkçe pop ve arabesk müzik video yayını"),
            (14, 0, "Number1 Türk Yayını", "Türkçe pop ve arabesk müzik video yayını"),
            (16, 0, "Number1 Türk Yayını", "Türkçe pop ve arabesk müzik video yayını"),
            (18, 0, "Number1 Türk Yayını", "Türkçe pop ve arabesk müzik video yayını"),
            (20, 0, "Number1 Türk Yayını", "Türkçe pop ve arabesk müzik video yayını"),
            (22, 0, "Number1 Türk Yayını", "Türkçe pop ve arabesk müzik video yayını"),
        ],
    },
    "tr.nr1ask": {
        "tz": IST_TZ,
        "daily": [
            ( 0, 0, "Romantik Türkçe Müzik Yayını", "Aşk şarkıları ve romantik Türkçe müzik video yayını"),
            ( 2, 0, "Romantik Türkçe Müzik Yayını", "Aşk şarkıları ve romantik Türkçe müzik video yayını"),
            ( 4, 0, "Romantik Türkçe Müzik Yayını", "Aşk şarkıları ve romantik Türkçe müzik video yayını"),
            ( 6, 0, "Romantik Türkçe Müzik Yayını", "Aşk şarkıları ve romantik Türkçe müzik video yayını"),
            ( 8, 0, "Romantik Türkçe Müzik Yayını", "Aşk şarkıları ve romantik Türkçe müzik video yayını"),
            (10, 0, "Romantik Türkçe Müzik Yayını", "Aşk şarkıları ve romantik Türkçe müzik video yayını"),
            (12, 0, "Romantik Türkçe Müzik Yayını", "Aşk şarkıları ve romantik Türkçe müzik video yayını"),
            (14, 0, "Romantik Türkçe Müzik Yayını", "Aşk şarkıları ve romantik Türkçe müzik video yayını"),
            (16, 0, "Romantik Türkçe Müzik Yayını", "Aşk şarkıları ve romantik Türkçe müzik video yayını"),
            (18, 0, "Romantik Türkçe Müzik Yayını", "Aşk şarkıları ve romantik Türkçe müzik video yayını"),
            (20, 0, "Romantik Türkçe Müzik Yayını", "Aşk şarkıları ve romantik Türkçe müzik video yayını"),
            (22, 0, "Romantik Türkçe Müzik Yayını", "Aşk şarkıları ve romantik Türkçe müzik video yayını"),
        ],
    },
    "tr.nr1dance": {
        "tz": IST_TZ,
        "daily": [
            ( 0, 0, "NR1 Dance Yayını", "Dance, elektronik ve club müzik video yayını"),
            ( 2, 0, "NR1 Dance Yayını", "Dance, elektronik ve club müzik video yayını"),
            ( 4, 0, "NR1 Dance Yayını", "Dance, elektronik ve club müzik video yayını"),
            ( 6, 0, "NR1 Dance Yayını", "Dance, elektronik ve club müzik video yayını"),
            ( 8, 0, "NR1 Dance Yayını", "Dance, elektronik ve club müzik video yayını"),
            (10, 0, "NR1 Dance Yayını", "Dance, elektronik ve club müzik video yayını"),
            (12, 0, "NR1 Dance Yayını", "Dance, elektronik ve club müzik video yayını"),
            (14, 0, "NR1 Dance Yayını", "Dance, elektronik ve club müzik video yayını"),
            (16, 0, "NR1 Dance Yayını", "Dance, elektronik ve club müzik video yayını"),
            (18, 0, "NR1 Dance Yayını", "Dance, elektronik ve club müzik video yayını"),
            (20, 0, "NR1 Dance Yayını", "Dance, elektronik ve club müzik video yayını"),
            (22, 0, "NR1 Dance Yayını", "Dance, elektronik ve club müzik video yayını"),
        ],
    },
    "tr.nr1damar": {
        "tz": IST_TZ,
        "daily": [
            ( 0, 0, "Rap Müzik Yayını", "Rap, hip-hop ve damar müzik video yayını"),
            ( 2, 0, "Rap Müzik Yayını", "Rap, hip-hop ve damar müzik video yayını"),
            ( 4, 0, "Rap Müzik Yayını", "Rap, hip-hop ve damar müzik video yayını"),
            ( 6, 0, "Rap Müzik Yayını", "Rap, hip-hop ve damar müzik video yayını"),
            ( 8, 0, "Rap Müzik Yayını", "Rap, hip-hop ve damar müzik video yayını"),
            (10, 0, "Rap Müzik Yayını", "Rap, hip-hop ve damar müzik video yayını"),
            (12, 0, "Rap Müzik Yayını", "Rap, hip-hop ve damar müzik video yayını"),
            (14, 0, "Rap Müzik Yayını", "Rap, hip-hop ve damar müzik video yayını"),
            (16, 0, "Rap Müzik Yayını", "Rap, hip-hop ve damar müzik video yayını"),
            (18, 0, "Rap Müzik Yayını", "Rap, hip-hop ve damar müzik video yayını"),
            (20, 0, "Rap Müzik Yayını", "Rap, hip-hop ve damar müzik video yayını"),
            (22, 0, "Rap Müzik Yayını", "Rap, hip-hop ve damar müzik video yayını"),
        ],
    },

    # ── MED MÜZİK TV — 2 saatlik döngü, 7/24 ────────────────────
    "tr.medmuziktv": {
        "tz": IST_TZ,
        "daily": [
            ( 0,  0, "Müzik Yayını", "Çeşitli sanatçılardan Kürtçe müzik yayını"),
            ( 2,  0, "Müzik Yayını", "Çeşitli sanatçılardan Kürtçe müzik yayını"),
            ( 4,  0, "Müzik Yayını", "Çeşitli sanatçılardan Kürtçe müzik yayını"),
            ( 6,  0, "Müzik Yayını", "Çeşitli sanatçılardan Kürtçe müzik yayını"),
            ( 8,  0, "Müzik Yayını", "Çeşitli sanatçılardan Kürtçe müzik yayını"),
            (10,  0, "Müzik Yayını", "Çeşitli sanatçılardan Kürtçe müzik yayını"),
            (12,  0, "Müzik Yayını", "Çeşitli sanatçılardan Kürtçe müzik yayını"),
            (14,  0, "Müzik Yayını", "Çeşitli sanatçılardan Kürtçe müzik yayını"),
            (16,  0, "Müzik Yayını", "Çeşitli sanatçılardan Kürtçe müzik yayını"),
            (18,  0, "Müzik Yayını", "Çeşitli sanatçılardan Kürtçe müzik yayını"),
            (20,  0, "Müzik Yayını", "Çeşitli sanatçılardan Kürtçe müzik yayını"),
            (22,  0, "Müzik Yayını", "Çeşitli sanatçılardan Kürtçe müzik yayını"),
        ],
    },

    # ── GÜLDÜR GÜLDÜR TV — 2 saatlik döngü, iki farklı EPG ───────
    "tr.guldurguldur": {
        "tz": IST_TZ,
        "daily": [
            (h, 0,
             "Güldür Güldür Show",
             ("BKM imzalı, 2013'ten bu yana kesintisiz güldüren efsane program. "
              "Ali Sunal ve güçlü kadrosuyla aile, aşk, teknoloji ve futboldan "
              "sketçler... Türk mizahının günümüzdeki en parlak yüzü perdede."
              if (h // 2) % 2 == 0 else
              "Güldür Güldür Show — gülmek için bin bir neden. "
              "Ali Sunal'ın liderliğinde kalabalık ve enerjik bir ekip, "
              "hayatın her köşesinden kesitler sunar. Show TV'nin vazgeçilmezi, "
              "her yaştan izleyicinin favorisi bu kanalda aralıksız yayında.")
            ) for h in range(0, 24, 2)
        ],
    },

    # ── LEYLA İLE MECNUN TV — 2 saatlik döngü, iki farklı EPG ────
    "tr.leylaileMecnun": {
        "tz": IST_TZ,
        "daily": [
            (h, 0,
             "Leyla ile Mecnun",
             ("2011'de TRT'de başlayan, Ali Atay ve Ezgi Asaroğlu'nun canlandırdığı "
              "efsane absürt komedi... Beşik kertmesi iki ruhun aşkı, ak sakallı dede "
              "ve Kireçburnu sokaklarında geçen olağanüstü bir hikaye. "
              "Onur Ünlü imzasıyla Türk televizyonunun en özgün yapımlarından biri."
              if (h // 2) % 2 == 0 else
              "Mecnun seviyor, Leyla biliyor, evren komplo kuruyor. "
              "Absürt, dokunaklı ve tamamen kendine özgü bir dizi — Leyla ile Mecnun. "
              "3 sezon, sayısız gülüş ve unutulmaz sahneleriyle bugün de perdede.")
            ) for h in range(0, 24, 2)
        ],
    },

    # ── YEDİ NUMARA TV — 2 saatlik döngü, iki farklı EPG ─────────
    "tr.yedinumara": {
        "tz": IST_TZ,
        "daily": [
            (h, 0,
             "Yedi Numara — Komedi Dizisi",
             ("2000-2003 yılları arasında 92 bölüm yayınlanan sevilen Türk komedi dizisi. "
              "Üniversite öğrencisi dört kız, taşradan gelen erkek komşuları ve "
              "7 numaralı ahşap ev... Farklı dünyaların bir arada yarattığı gülmece, "
              "bugün de taze ve sıcak."
              if (h // 2) % 2 == 0 else
              "Zeliha, Vahit, Sabit ve 7 numaralı evin birbirinden renkli sakinleri... "
              "Türk televizyonunun en sevilen sitcom'larından Yedi Numara, "
              "gülüşlerimizi geri çağırıyor. Komşuluk, dostluk ve tükenmeyen neşe — "
              "kesintisiz bölümler bu kanalda.")
            ) for h in range(0, 24, 2)
        ],
    },

    # ── ŞABAN TV 3 — 2 saatlik döngü, iki farklı EPG ────────────
    "tr.kemalsunal": {
        "tz": IST_TZ,
        "daily": [
            (h, 0,
             "Şaban'ın Dünyası",
             ("Üçüncü perde, aynı sevgi. Kemal Sunal'ın yarattığı Şaban evreni "
              "bu kanalda da yaşıyor. Safiyetin, dürüstlüğün ve halk mizahının "
              "en güzel örnekleri — Türk sinemasının vazgeçilmez hazineleri perdede."
              if (h // 2) % 2 == 0 else
              "Kemal Sunal'sız Türk sineması düşünülemez. "
              "Şaban TV 3'te o ikonik gülüş, o tanıdık yüz yine karşınızda. "
              "Gülmek, düşünmek, hatırlamak için — kesintisiz Kemal Sunal filmleri.")
            ) for h in range(0, 24, 2)
        ],
    },

    # ── ŞABAN TV 2 — 2 saatlik döngü, iki farklı EPG ────────────
    "tr.sabana2": {
        "tz": IST_TZ,
        "daily": [
            (h, 0,
             "Kemal Sunal Klasikleri",
             ("Şaban'ın ikinci perdesi açılıyor. Kemal Sunal'ın ustalıkla canlandırdığı "
              "o masum, saf ve her zaman kazanan karakteriyle dolu filmler burada. "
              "Güldürürken bir şeyler öğreten, eğlendirirken dokunduran Türk sinemasının incileri."
              if (h // 2) % 2 == 0 else
              "Kemal Sunal bir fenomendi — sadece güldürmedi, ayna tuttu. "
              "Toplumun her kesiminden bir his, her filmde tanıdık bir yüz. "
              "Şaban TV 2'de gece boyunca devam eden o efsanevi yolculuk sizi bekliyor.")
            ) for h in range(0, 24, 2)
        ],
    },

    # ── ŞABAN TV — 2 saatlik döngü, iki farklı EPG ───────────────
    "tr.sabantv": {
        "tz": IST_TZ,
        "daily": [
            (h, 0,
             "Kemal Sunal'ın Şaban'ı",
             ("Türk sinemasının en sevilen karakteri Şaban, yeniden perdede. "
              "Kemal Sunal'ın eşsiz komedisi, zamana meydan okuyan o saf ve dürüst bakış... "
              "Her sahnede güldüren, her replikte içe işleyen bir Şaban filmi sizi bekliyor."
              if (h // 2) % 2 == 0 else
              "Şaban sadece bir karakter değil, bir halk masalıdır. "
              "Kemal Sunal'ın kaleme aldığı o eşsiz yüz ifadesiyle, "
              "Türkiye'nin dört bir yanında gülücükler yeşerdi. "
              "Bu gece de Şaban var — perdede, kalpte, hatırada.")
            ) for h in range(0, 24, 2)
        ],
    },

    # ── GÜLŞAH FİLM TV — 2 saatlik döngü, iki farklı EPG ────────
    "tr.gulsahkemal": {
        "tz": IST_TZ,
        "daily": [
            (h, 0,
             "Kemal Sunal Filmleri",
             ("1974'te İstanbul'da kurulan Gülşah Film'in efsanevi yapımları... "
              "Kemal Sunal'ın Türk sinemasına kazandırdığı unutulmaz karakterler, "
              "güldürürken düşündüren hikayeler. Şaban'dan İnek Şaban'a, "
              "Neşeli Günler'den Devlerin Aşkı'na — hep güldük, hep sevdik."
              if (h // 2) % 2 == 0 else
              "Gülşah Film imzasıyla Türk sinemasının altın sayfaları... "
              "Kemal Sunal'ın milyonlara dokunan performansları, zamanın ötesinde yaşayan yapımlar. "
              "Her filmde bir dönem, her sahnede bir his — Gülşah Film'den seçkin yapımlar perdede.")
            ) for h in range(0, 24, 2)
        ],
    },

    # ── YEŞİLÇAM TV — 2 saatlik döngü, iki farklı EPG ───────────
    "tr.yesilcam": {
        "tz": IST_TZ,
        "daily": [
            (h, 0,
             "Yeşilçam'dan Seçmeler" if (h // 2) % 2 == 0 else "Nostaljik Türk Sineması",
             ("Türk sinemasının efsanevi yapımları... Kemal Sunal'dan Münir Özkul'a, "
              "İlyas Salman'dan Adile Naşit'e uzanan kadrosuyla Yeşilçam'ın ölümsüz filmleri. "
              "Güldürürken düşündüren, eğlendirirken dokunduran yapımlar."
              if (h // 2) % 2 == 0 else
              "Anadolu'nun sesi, halkın sineması... Yeşilçam'ın renkli dünyasından "
              "dram, komedi ve macera bir arada. Jenerasyondan jenerasyona aktarılan "
              "film mirası, bugün de perdede yaşıyor.")
            ) for h in range(0, 24, 2)
        ],
    },

    # ── ÇİÇEK TAKSİ TV — 2 saatlik döngü ────────────────────────
    "tr.cicektaksi": {
        "tz": IST_TZ,
        "daily": [
            (h, 0,
             "Çiçek Taksi — Efsane Dizi",
             ("1995'te ATV'de başlayan, 367 bölümle Türk televizyon tarihine geçen efsane dizi. "
              "Erol Günaydın'ın Ramazan'ıyla İstanbul'un bir taksi durağında "
              "güldüren, duygulandıran hayat hikayeleri yeniden perdede."
              if (h // 2) % 2 == 0 else
              "Taksi şoförlerinin ailesi, bitmez derdi ve sonsuz neşesiyle "
              "Çiçek Taksi durağından selamlar. 7 sezon, 367 bölüm, "
              "binlerce gülümseme — Türk televizyonunun klasiği bu kanalda.")
            ) for h in range(0, 24, 2)
        ],
    },

    # ── SEKSENLER TV — 2 saatlik döngü ───────────────────────────
    "tr.seksenler": {
        "tz": IST_TZ,
        "daily": [
            (h, 0,
             "Seksenler — Nostaljik Dönem Dizisi",
             ("2012'de TRT 1'de başlayan, 9 sezon 655 bölüm süren nostaljik dönem komedisi. "
              "Rasim Öztekin ve kadrosuyla 1980'lerin İstanbul mahallesinde "
              "bir ailenin sıcak ve eğlenceli günlük yaşamı."
              if (h // 2) % 2 == 0 else
              "Seksenler — o yıllar, o mahalle, o insanlar. "
              "Birol Güven imzalı yapım, hem bir dönemin belgesel tadındaki aynası "
              "hem de tüm ailelerin bir arada keyifle izleyeceği sıcak bir komedi.")
            ) for h in range(0, 24, 2)
        ],
    },

    # ── AVRUPA YAKASI TV — 2 saatlik döngü ───────────────────────
    "tr.avrupayakasitv": {
        "tz": IST_TZ,
        "daily": [
            (h, 0,
             "Avrupa Yakası — Şehirli Komedi",
             ("Gülse Birsel'in kaleme aldığı, 2004-2009 yılları arasında 190 bölüm yayınlanan "
              "efsane sitcom. Gazanfer Özcan, Ata Demirer, Engin Günaydın... "
              "Nişantaşı'ndan İstanbul'un renkli şehir hayatına alaycı ama sevecen bir bakış."
              if (h // 2) % 2 == 0 else
              "Moda, magazin, komşuluk ve şehirli kaosun içinde Avrupa Yakası. "
              "6 sezon boyunca Türkiye'yi güldüren, ödüller kazanan yapım — "
              "Gülse Birsel'in tükenmeyen kalemi ve muhteşem kadrosuyla bu kanalda.")
            ) for h in range(0, 24, 2)
        ],
    },

    # ── YALAN DÜNYA TV — 2 saatlik döngü ─────────────────────────
    "tr.yalandunayatv": {
        "tz": IST_TZ,
        "daily": [
            (h, 0,
             "Yalan Dünya — Kanal D Klasiği",
             ("2012-2014 yılları arasında Kanal D'de 90 bölüm yayınlanan sevilen komedi. "
              "Altan Erkekli, Füsun Demirel ve Olgun Şimşek... "
              "Cihangir'de bir arada yaşamak zorunda kalan büyük bir ailenin "
              "birbirinden komik ve dokunaklı hikayeleri."
              if (h // 2) % 2 == 0 else
              "Antakya'dan Cihangir'e taşınan Kocabaş ailesi, "
              "gelenekler ve modern hayat arasında sıkışmış karakterler... "
              "Yalan Dünya — 4 sezon boyunca güldüren, düşündüren, "
              "ev halkını bir araya getiren o sıcak dizi bu kanalda.")
            ) for h in range(0, 24, 2)
        ],
    },

    # ── ALEMİN KRALI TV — 2 saatlik döngü ────────────────────────
    "tr.aleminkralitv": {
        "tz": IST_TZ,
        "daily": [
            (h, 0,
             "Alemin Kıralı — Şafak Sezer ile",
             ("Şafak Sezer ve Oya Başar'ın buluştuğu, 2011-2013 yılları arasında "
              "67 bölüm yayınlanan ATV komedisi. Petshop sahibi Aslan'ın "
              "altı kadının yaşadığı evde içgüveysi olarak geçen çileli ama eğlenceli hayatı."
              if (h // 2) % 2 == 0 else
              "Alemin Kıralı olmak kolay değil — özellikle de kayınvalidenin "
              "gözüne girmeye çalışırken. Şafak Sezer'in eşsiz komedisiyle, "
              "Türk sitcom tarihinin en sevilen yapımlarından biri bu kanalda.")
            ) for h in range(0, 24, 2)
        ],
    },

    # ── AVŞAR FİLM TV — 2 saatlik döngü, iki farklı EPG ─────────
    "tr.avsarfilmtv": {
        "tz": IST_TZ,
        "daily": [
            (h, 0,
             "Avşar Film Seçkisi",
             ("1984'te Şükrü Avşar tarafından kurulan Avşar Film'in büyüleyici yapımları. "
              "Babam ve Oğlum'dan Karagül'e, Zalim İstanbul'dan Fazilet Hanım'a uzanan "
              "Türk televizyonunun en kalburüstü yapımları bu kanalda."
              if (h // 2) % 2 == 0 else
              "Duygu, heyecan ve nitelikli anlatım — Avşar Film'in imzası bu. "
              "Türkiye'nin dört bir yanına dokunan hikâyeler, "
              "ödüllü yapımlar ve seçkin kadrosuyla Avşar Film yapımları perdede.")
            ) for h in range(0, 24, 2)
        ],
    },

    # ── ARZU FİLM TV — 2 saatlik döngü ──────────────────────────
    "tr.arzufilm": {
        "tz": IST_TZ,
        "daily": [(h, 0, "Arzu Film Yapımı Filmler",
            "1964'te Ertem Eğilmez tarafından kurulan Arzu Film'in efsanevi yapımları... "
            "Hababam Sınıfı'ndan Tarkan'a, Maskeli Beşler'den unutulmaz güldürülere uzanan "
            "Türk sinemasının altın çağından seçkin yapımlar. Arzu Film imzasıyla, "
            "Anadolu'nun ruhunu yansıtan eserler perdede."
        ) for h in range(0, 24, 2)],
    },

    # ── RİZE TÜRK — 2 saatlik film döngüsü ──────────────────────
    "tr.rizeturk": {
        "tz": IST_TZ,
        "daily": [(h, 0, "Seçkin Film Yayını", "Özenle seçilmiş filmler ve yapımlarla dolu, estetik bir sinema deneyimi.") for h in range(0, 24, 2)],
    },

    # ── CAN TV — 2 saatlik müzik döngüsü ────────────────────────
    "tr.cantv": {
        "tz": IST_TZ,
        "daily": [(h, 0, "Müzik Yayını", "Seçme Halk Müziği Yayını") for h in range(0, 24, 2)],
    },

    # ── CEM TV — 2 saatlik müzik döngüsü ────────────────────────
    "tr.cemtv": {
        "tz": IST_TZ,
        "daily": [(h, 0, "Müzik Yayını", (
            "KAMUOYUNUN DİKKATİNE…\n\n"
            "SEVGİNİN, HOŞGÖRÜNÜN VE HAKİKATİN SESİ CEM TELEVİZYONU, YAYIN HAYATINA BAŞLADI.\n\n"
            "ANADOLU'NUN KADİM KÜLTÜRÜNÜ, SÖNMEYEN BİR MEŞALE GİBİ GELECEĞE TAŞIYAN CEM TELEVİZYONU, "
            "GEÇMİŞİN MİRASINI MODERN YAYINCILIK ANLAYIŞIYLA BİRLEŞTİREREK, YENİ YÖNETİM KADROSU İLE EKRANLARDAKİ YERİNİ ALDI.\n\n"
            "TOPLUMUN TÜMÜNÜ KAPSAYAN, YAYINLARIYLA TÜRKİYE'Yİ VE DÜNYAYI KUCAKLAYAN, BİRLİK VE BERABERLİĞİ ÖN PLANA ALMAYI "
            "HEDEFLEYEN CEM TELEVİZYONU, KÜLTÜREL KARDEŞLİĞİMİZİ PEKİŞTİREN YAPISIYLA İZLEYİCİSİYLE BULUŞUYOR.\n\n"
            "BÖLEN DEĞİL BİRLEŞTİREN, SEVGİYİ YÜCELTEN, 7'DEN 70'E HERKESİ KUCAKLAYAN YAYINCILIK HEDEFİYLE YOLA ÇIKAN "
            "CEM TELEVİZYONU, BİRBİRİNDEN ÖZEL PROGRAMLARA DA İMZA ATMAYA HAZIRLANIYOR.\n\n"
            "ÖZLEM BİTİYOR…\nCEM TV \"SİZİN SESİNİZ\"\n\nSAYGILARIMIZLA,\nCEM TELEVİZYONU YÖNETİM KURULU"
        )) for h in range(0, 24, 2)],
    },

    # ── NEO HABER — her gün aynı, Türkiye saati ──────────────────
    "tr.neohabertv": {
        "tz": IST_TZ,
        "daily": [
            ( 8,  0, "Uyanma Servisi",        "Kutluhan Nesil ile"),
            (11,  0, "Ekonomi Ajansı",         "Hanzade Avcıoğlu ile"),
            (12,  0, "Gün Ortası",             "Senem Gökdağ ile"),
            (14,  0, "Aramızda Kalsın",        "Esra Kavrukkoca ile"),
            (15,  0, "Dokun Hayata",           "Elif Akar ile"),
            (17,  0, "Beyaz Masa",             "Ertuğrut Turan ile"),
            (18, 30, "Ana Haber",              "Alper Esin Baran ile"),
            (19, 30, "Neo Haber Akşam Kuşağı", "Neo Haber akşam yayını"),
            (23,  0, "Gece Kuşağı Yayını",    "Neo Haber gece yayını"),
        ],
    },

    # ── MCE TV — haftalık, Istanbul saati ────────────────────────
    "tr.mceutv": {
        "tz": IST_TZ,
        "days": {
            0: [  # PAZARTESİ
                ( 5,  0, "Hatim Saati"),
                ( 6,  0, "Dua Vakti"),
                ( 6, 30, "Efendimiz (s.a.v.)"),
                ( 7,  0, "Dini Programlar"),
                ( 7, 30, "Çocuk Kuşağı"),
                ( 8, 30, "Haber Yorum"),
                ( 9, 30, "Çınarın Gölgesinde"),
                (10, 15, "Aile ve Çocuk Eğitimi Kuşağı"),
                (11,  0, "Mavi Rüya"),
                (12,  0, "Haberler"),
                (14,  0, "Yemek Programı - Pasta Börek"),
                (15, 15, "İki Dünya Arasında"),
                (16, 15, "Gençlere Özel"),
                (16, 35, "Çocuk Kuşağı"),
                (17,  0, "Haber-Yorum"),
                (18,  0, "TV Filmi"),
                (19,  0, "Kültür-Eğitim"),
                (19, 30, "Haber-Yorum"),
                (21,  0, "Ana Haber"),
                (22,  0, "Ekip 1"),
                (23,  0, "Bamteli"),
                (23, 30, "Kutup Yıldızları"),
                ( 0,  0, "Gece Haberleri"),
                ( 2,  0, "Beşinci Boyut"),
                ( 3,  0, "Almanca + İngilizce"),
                ( 3, 45, "Ana Dizi Kuşağı"),
            ],
            1: [  # SALI
                ( 5,  0, "Hatim Saati"),
                ( 6,  0, "Dua Vakti"),
                ( 6, 30, "Efendimiz (s.a.v.)"),
                ( 7,  0, "Dini Programlar"),
                ( 7, 30, "Çocuk Kuşağı"),
                ( 8, 30, "Haber Yorum"),
                ( 9, 30, "Çınarın Gölgesinde"),
                (10, 15, "Aile ve Çocuk Eğitimi Kuşağı"),
                (11,  0, "Mavi Rüya"),
                (12,  0, "Haberler"),
                (14,  0, "Yemek Programı - Pasta Börek"),
                (15, 15, "İki Dünya Arasında"),
                (16, 15, "Gençlere Özel"),
                (16, 35, "Çocuk Kuşağı"),
                (17,  0, "Haber-Yorum"),
                (18,  0, "TV Filmi"),
                (19,  0, "Kültür-Eğitim"),
                (19, 30, "Haber-Yorum"),
                (21,  0, "Ana Haber"),
                (22,  0, "Kendi Okulumüza Doğru"),
                (23,  0, "Bamteli"),
                (23, 30, "Nurdan Hüzmeler"),
                ( 0,  0, "Gece Haberleri"),
                ( 2,  0, "Beşinci Boyut"),
                ( 3,  0, "Almanca + İngilizce"),
                ( 3, 45, "Ana Dizi Kuşağı"),
            ],
            2: [  # ÇARŞAMBA
                ( 5,  0, "Hatim Saati"),
                ( 6,  0, "Dua Vakti"),
                ( 6, 30, "Efendimiz (s.a.v.)"),
                ( 7,  0, "Dini Programlar"),
                ( 7, 30, "Çocuk Kuşağı"),
                ( 8, 30, "Haber Yorum"),
                ( 9, 30, "Çınarın Gölgesinde"),
                (10, 15, "Aile ve Çocuk Eğitimi Kuşağı"),
                (11,  0, "Mavi Rüya"),
                (12,  0, "Haberler"),
                (14,  0, "Yemek Programı - Pasta Börek"),
                (15, 15, "İki Dünya Arasında"),
                (16, 15, "Gençlere Özel"),
                (16, 35, "Çocuk Kuşağı"),
                (17,  0, "Haber-Yorum"),
                (18,  0, "TV Filmi"),
                (19,  0, "Kültür-Eğitim"),
                (19, 30, "Haber-Yorum"),
                (21,  0, "Ana Haber"),
                (22,  0, "Ve İnsan Aldandı"),
                (23,  0, "Bamteli"),
                (23, 30, "Etik Politik"),
                ( 0,  0, "Gece Haberleri"),
                ( 2,  0, "Beşinci Boyut"),
                ( 3,  0, "Almanca + İngilizce"),
                ( 3, 45, "Ana Dizi Kuşağı"),
            ],
            3: [  # PERŞEMBE
                ( 5,  0, "Hatim Saati"),
                ( 6,  0, "Dua Vakti"),
                ( 6, 30, "Efendimiz (s.a.v.)"),
                ( 7,  0, "Dini Programlar"),
                ( 7, 30, "Çocuk Kuşağı"),
                ( 8, 30, "Haber Yorum"),
                ( 9, 30, "Çınarın Gölgesinde"),
                (10, 15, "Aile ve Çocuk Eğitimi Kuşağı"),
                (11,  0, "Mavi Rüya"),
                (12,  0, "Haberler"),
                (14,  0, "Yemek Programı - Pasta Börek"),
                (15, 15, "İki Dünya Arasında"),
                (16, 15, "Gençlere Özel"),
                (16, 35, "Çocuk Kuşağı"),
                (17,  0, "Haber-Yorum"),
                (18,  0, "TV Filmi"),
                (19,  0, "Kültür-Eğitim"),
                (19, 30, "Haber-Yorum"),
                (21,  0, "Ana Haber"),
                (22,  0, "Büyük Buluşma"),
                (23,  0, "Bamteli"),
                (23, 30, "Dini Aktüel"),
                ( 0,  0, "Gece Haberleri"),
                ( 2,  0, "Beşinci Boyut"),
                ( 3,  0, "Almanca + İngilizce"),
                ( 3, 45, "Ana Dizi Kuşağı"),
            ],
            4: [  # CUMA
                ( 5,  0, "Hatim Saati"),
                ( 6,  0, "Dua Vakti"),
                ( 6, 30, "Efendimiz (s.a.v.)"),
                ( 7,  0, "Dini Programlar"),
                ( 7, 30, "Çocuk Kuşağı"),
                ( 8, 30, "Haber Yorum"),
                ( 9, 30, "Çınarın Gölgesinde"),
                (10, 15, "Aile ve Çocuk Eğitimi Kuşağı"),
                (11,  0, "Mavi Rüya"),
                (12,  0, "Haberler"),
                (14,  0, "Yemek Programı - Pasta Börek"),
                (15, 15, "İki Dünya Arasında"),
                (16, 15, "Gençlere Özel"),
                (16, 35, "Çocuk Kuşağı"),
                (17,  0, "Haber-Yorum"),
                (18,  0, "TV Filmi"),
                (19,  0, "Kültür-Eğitim"),
                (19, 30, "Haber-Yorum"),
                (21,  0, "Ana Haber"),
                (22,  0, "Güz Gülleri"),
                (23,  0, "Bamteli"),
                (23, 30, "Nurdan Hüzmeler"),
                ( 0,  0, "Gece Haberleri"),
                ( 2,  0, "Beşinci Boyut"),
                ( 3,  0, "Almanca + İngilizce"),
                ( 3, 45, "Ana Dizi Kuşağı"),
            ],
            5: [  # CUMARTESİ
                ( 5,  0, "Hatim Saati"),
                ( 6,  0, "Dua Vakti"),
                ( 6, 30, "Efendimiz (s.a.v.)"),
                ( 7,  0, "Dini Programlar"),
                ( 7, 30, "Çocuk Kuşağı"),
                ( 8, 30, "Haber Yorum"),
                ( 9, 30, "Çınarın Gölgesinde"),
                (10, 15, "Aile ve Çocuk Eğitimi Kuşağı"),
                (11,  0, "Mavi Rüya"),
                (12,  0, "Haberler"),
                (14,  0, "Yemek Programı - Yeşil Elma"),
                (15, 15, "İki Dünya Arasında"),
                (16, 15, "Gençlere Özel"),
                (16, 35, "Çocuk Kuşağı"),
                (17,  0, "Haber-Yorum"),
                (18,  0, "TV Filmi"),
                (19,  0, "Kültür-Eğitim"),
                (19, 30, "Haber-Yorum"),
                (21,  0, "Ana Haber"),
                (22,  0, "Küçük Gelin"),
                (23,  0, "Bamteli"),
                (23, 30, "Kitabın Ortası"),
                ( 0,  0, "Gece Haberleri"),
                ( 2,  0, "Beşinci Boyut"),
                ( 3,  0, "Almanca + İngilizce"),
                ( 3, 45, "Ana Dizi Kuşağı"),
            ],
            6: [  # PAZAR
                ( 5,  0, "Hatim Saati"),
                ( 6,  0, "Dua Vakti"),
                ( 6, 30, "Efendimiz (s.a.v.)"),
                ( 7,  0, "Dini Programlar"),
                ( 7, 30, "Çocuk Kuşağı"),
                ( 8, 30, "Haber Yorum"),
                ( 9, 30, "Çınarın Gölgesinde"),
                (10, 15, "Aile ve Çocuk Eğitimi Kuşağı"),
                (11,  0, "Mavi Rüya"),
                (12,  0, "Haberler"),
                (14,  0, "Yemek Programı - Yeşil Elma"),
                (15, 15, "İki Dünya Arasında"),
                (16, 15, "Gençlere Özel"),
                (16, 35, "Çocuk Kuşağı"),
                (17,  0, "Haber-Yorum"),
                (18,  0, "TV Filmi"),
                (19,  0, "Kültür-Eğitim"),
                (19, 30, "Haber-Yorum"),
                (21,  0, "Ana Haber"),
                (22,  0, "Ritmini Arayan Kalpler"),
                (23,  0, "Bamteli"),
                (23, 30, "Dünyalem"),
                ( 0,  0, "Gece Haberleri"),
                ( 2,  0, "Beşinci Boyut"),
                ( 3,  0, "Almanca + İngilizce"),
                ( 3, 45, "Ana Dizi Kuşağı"),
            ],
        },
    },

    # ── KANAL AVRUPA — haftalık, Almanya saati ───────────────────
    "tr.kanalavrupatv": {
        "tz": DE_TZ,
        "days": {
        0: [  # PAZARTESİ
            ( 6,  0, "Klip Saati"),
            ( 6, 45, "Yaşayan Tarih"),
            ( 7, 30, "Anahaber"),
            ( 8, 45, "Bakış Açısı"),
            (10,  0, "Ege Gündemİ"),
            (11, 45, "Estetik ve Sağlık"),
            (13,  0, "Anahaber"),
            (13, 45, "Türk Dünyası"),
            (15,  0, "Kadınca"),
            (16, 45, "Avrupa Klip Magazin"),
            (17, 30, "Anahaber"),
            (18, 15, "Bildung & Beruf"),
            (19, 45, "100 Yıllık Türküler"),
            (21,  0, "Anahaber"),
            (22, 15, "Spor Avrupa"),
            (23, 30, "Anahaber"),
            ( 0, 30, "Bakış Açısı"),
            ( 2, 15, "Bizsiz Olmaz 1"),
            ( 3, 45, "Namekan Türküler"),
            ( 5,  0, "Türkülerimiz"),
        ],
        1: [  # SALI
            ( 6,  0, "Klip Saati"),
            ( 6, 45, "Belgesel"),
            ( 7, 30, "Anahaber"),
            ( 8, 45, "Sivil İnsiyatif"),
            (10,  0, "Berlin Gündemi"),
            (11, 45, "Spor Avrupa"),
            (13,  0, "Anahaber"),
            (13, 45, "Türk Dünyası"),
            (15,  0, "100 Yıllık Türküler"),
            (16, 45, "Avrupa Klip Magazin"),
            (17, 30, "Anahaber"),
            (18, 15, "Sağlık Saati"),
            (19, 45, "Karadeniz Show"),
            (21,  0, "Anahaber"),
            (22, 15, "Ersoy Show"),
            (23, 30, "Anahaber"),
            ( 0, 30, "Sivil İnsiyatif"),
            ( 2, 15, "Bizsiz Olmaz 2"),
            ( 3, 45, "Asrın Türküleri"),
            ( 5,  0, "Türkülerimiz"),
        ],
        2: [  # ÇARŞAMBA
            ( 6,  0, "Klip Saati"),
            ( 7, 30, "Anahaber"),
            ( 8, 45, "Avrupa Baskısı"),
            (10,  0, "Sağlıklı Yaşamın Sırları"),
            (11, 45, "Karadeniz Show"),
            (13,  0, "Anahaber"),
            (13, 45, "Türk Dünyası"),
            (15,  0, "Ersoy Show"),
            (16, 45, "Avrupa Klip Magazin"),
            (17, 30, "Anahaber"),
            (18, 15, "Rota"),
            (19, 45, "Her Türkü Bir Hikaye"),
            (21,  0, "Anahaber"),
            (22, 15, "İş Dünyası"),
            (23, 30, "Anahaber"),
            ( 0, 30, "Avrupa Baskısı"),
            ( 2, 15, "Avrupalı Türkler"),
            ( 3, 45, "Yolcu Türküsü"),
            ( 5,  0, "Türkülerimiz"),
        ],
        3: [  # PERŞEMBE
            ( 6,  0, "Klip Saati"),
            ( 7, 30, "Anahaber"),
            ( 8, 45, "Avrupa Arenası"),
            (10,  0, "Rota"),
            (11, 45, "Suskun Türküler"),
            (13,  0, "Anahaber"),
            (13, 45, "Türk Dünyası"),
            (15,  0, "İş Dünyası"),
            (16, 45, "Avrupa Klip Magazin"),
            (17, 30, "Anahaber"),
            (18, 15, "Sağlıklı Yaşamın Sırları"),
            (19, 45, "Anadolu Diyarı"),
            (21,  0, "Anahaber"),
            (22, 15, "Rahmet Vakti"),
            (23, 30, "Anahaber"),
            ( 0, 30, "Avrupa Arenası"),
            ( 2, 15, "Bizsiz Olmaz 1"),
            ( 3, 45, "Ay Dost"),
            ( 5,  0, "Türkülerimiz"),
        ],
        4: [  # CUMA
            ( 6,  0, "Klip Saati"),
            ( 7, 30, "Anahaber"),
            ( 8, 45, "Ateş Çemberi"),
            (10,  0, "Sağlıklı Yaşamın Sırları"),
            (11, 45, "Anadolu Diyarı"),
            (13,  0, "Anahaber"),
            (13, 45, "Türk Dünyası"),
            (15,  0, "Rahmet Vakti"),
            (16, 45, "Avrupa Klip Magazin"),
            (17, 30, "Anahaber"),
            (18, 15, "Ege Gündemi"),
            (19, 45, "Anadolu Rock"),
            (21,  0, "Anahaber"),
            (22, 15, "Hukuk Masası"),
            (23, 30, "Anahaber"),
            ( 0, 30, "Ateş Çemberi"),
            ( 2, 15, "Bizsiz Olmaz 2"),
            ( 3, 45, "Şarkılardan Fal Tutum"),
            ( 5,  0, "Türkülerimiz"),
        ],
        5: [  # CUMARTESİ
            ( 6,  0, "Klip Saati"),
            ( 6, 30, "Bizsiz Olmaz 1"),
            ( 6, 45, "Bizsiz Olmaz 1"),
            ( 7, 30, "Anahaber"),
            ( 8, 30, "İş Dünyası"),
            ( 9, 45, "Avrupa Masası"),
            (10,  0, "Yaşayan Tarih"),
            (10, 15, "Emin Adımlar"),
            (11, 45, "Hukuk Masası"),
            (13,  0, "Sağlık Saati"),
            (13, 30, "Kadınca"),
            (14, 45, "Brüksel Gündemi"),
            (15, 15, "Sağlıklı Yaşamın Sırları"),
            (16, 30, "Türk Dünyası"),
            (16, 45, "Sivil İnsiyatif"),
            (17, 45, "Suskun Türküler"),
            (18, 15, "Berlin Gündemi"),
            (19, 45, "Bakış Açısı"),
            (21,  0, "Anahaber"),
            (22, 15, "Avrupa Baskısı"),
            (23, 30, "Anahaber"),
            ( 0, 30, "Asrın Türküleri"),
            ( 2, 15, "Avrupalı Türkler"),
            ( 2, 30, "Bizsiz Olmaz 1"),
            ( 3, 45, "Tümence"),
            ( 5,  0, "Türkülerimiz"),
        ],
        6: [  # PAZAR
            ( 6,  0, "Klip Saati"),
            ( 6, 30, "Bizsiz Olmaz 2"),
            ( 6, 45, "Bizsiz Olmaz 2"),
            ( 7, 30, "Anahaber"),
            ( 8, 45, "Avrupa Masası"),
            (10, 15, "Emin Adımlar"),
            (11, 45, "Estetik ve Sağlık"),
            (13, 30, "Kadınca"),
            (15, 15, "Sağlıklı Yaşamın Sırları"),
            (16, 30, "Türk Dünyası"),
            (17, 45, "Suskun Türküler"),
            (19, 45, "Avrupa Arenası"),
            (21,  0, "Anahaber"),
            (21, 45, "Ateş Çemberi"),
            (23,  0, "Ekmek Teknesi"),
            (23, 30, "Anahaber"),
            ( 0, 45, "Asrın Türküleri"),
            ( 2, 30, "Bizsiz Olmaz 1"),
            ( 3, 45, "Bir Demet Türkü"),
            ( 5,  0, "Türkülerimiz"),
        ],
        },
    },
}


class StaticScheduleAdapter(BaseAdapter):
    prefix = "staticschedule"

    def fetch(self, source_id: str, channel_id: str) -> List[Programme]:
        schedule = SCHEDULES.get(source_id)
        if not schedule:
            return []
        return self._generate(schedule, channel_id)

    def _generate(self, schedule: dict, channel_id: str) -> List[Programme]:
        now = ist(datetime.now())
        out: List[Programme] = []
        sched_tz = schedule.get("tz", DE_TZ)

        now_local = now.astimezone(sched_tz)
        monday = (now_local - timedelta(days=now_local.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0)

        if "daily" in schedule:
            # Günlük döngü: her gün aynı, 4 hafta üret
            programs = schedule["daily"]
            for day_offset in range(-7, 22):
                day_base = monday + timedelta(days=day_offset)
                self._add_programs(programs, day_base, sched_tz, channel_id, out)
        else:
            # Haftalık döngü
            days = schedule.get("days", {})
            for week_offset in range(-1, 3):
                week_start = monday + timedelta(weeks=week_offset)
                for weekday, programs in days.items():
                    day_base = week_start + timedelta(days=weekday)
                    self._add_programs(programs, day_base, sched_tz, channel_id, out)

        return out

    def _add_programs(self, programs, day_base, sched_tz, channel_id, out):
        for entry in programs:
            h, m, title = entry[0], entry[1], entry[2]
            desc = entry[3] if len(entry) > 3 else None
            day = day_base + timedelta(days=1) if h < 6 else day_base
            start_dt = datetime(day.year, day.month, day.day, h, m,
                                tzinfo=sched_tz).astimezone(IST_TZ)
            out.append(Programme(
                channel_id=channel_id,
                start=start_dt,
                title=title,
                desc=desc,
                source=self.prefix,
            ))
