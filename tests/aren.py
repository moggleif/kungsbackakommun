"""Åren som bygget ger exempelbyn med de här raderna och inga andra (K60)."""

from kommunhandlingar.webbplats.arspann import arspann


def aren(rader) -> range:
    return arspann([r.ar for r in rader])
