"""Genere dist/muthur.ico : voyant MU-TH-UR (Python pur, sans bibliotheque externe).

Usage : python outils/creer_icone.py
Le fichier ICO contient plusieurs tailles (16 a 256 px), chacune encodee en PNG.
"""
import math
import struct
import zlib
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "dist" / "muthur.ico"


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def pixel(x, y, n):
    """Couleur RGBA d’un pixel : façade industrielle, témoin vert ambre et reflet."""
    c = (n - 1) / 2
    d = math.hypot(x - c, y - c) / (n / 2)   # 0 au centre, 1 au bord
    if d > 1:
        return (0, 0, 0, 0)
    edge = min(1.0, (1 - d) * n / 2)          # anticrenelage du bord
    if d > 0.86:                              # bague metal
        col = mix((70, 70, 72), (25, 25, 27), (d - 0.86) / 0.14)
    elif d > 0.80:                            # liseré noir
        col = (8, 8, 8)
    else:                                     # voyant : degrade radial
        r = d / 0.80
        stops = [(0, (224, 207, 150)), (0.10, (149, 171, 124)), (0.30, (81, 111, 82)),
                 (0.65, (32, 52, 37)), (1, (9, 14, 10))]
        for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
            if r <= p1:
                col = mix(c0, c1, (r - p0) / (p1 - p0))
                break
        # petit reflet en haut a droite
        hx, hy = x - (c + n * 0.17), y - (c - n * 0.2)
        if (hx / (n * 0.07)) ** 2 + (hy / (n * 0.04)) ** 2 < 1:
            col = mix(col, (238, 228, 188), 0.28)
    return (*col, round(255 * edge))


def png(n):
    raw = b"".join(b"\0" + b"".join(bytes(pixel(x, y, n)) for x in range(n)) for y in range(n))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 6, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def ico(sizes=(16, 24, 32, 48, 64, 128, 256)):
    images = [png(s) for s in sizes]
    head = struct.pack("<HHH", 0, 1, len(sizes))
    offset = 6 + 16 * len(sizes)
    entries = b""
    for s, img in zip(sizes, images):
        entries += struct.pack("<BBBBHHII", s % 256, s % 256, 0, 0, 1, 32, len(img), offset)
        offset += len(img)
    return head + entries + b"".join(images)


if __name__ == "__main__":
    OUT.write_bytes(ico())
    print("icone creee :", OUT)
