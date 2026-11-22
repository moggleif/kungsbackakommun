"""Krav: K1, K39 och K54 i docs/02-KRAV.md.
Test: tests/test_konfiguration.py."""

from dataclasses import dataclass
from datetime import date
from itertools import combinations

from kommunhandlingar import schema
from kommunhandlingar.fel import Konfigurationsfel

ORGANFALT = {
    "id",
    "namn",
    "fran",
    "till",
    "foregangare",
    "hor_till",
    "grupp",
    "sammantradessidor",
}


@dataclass(frozen=True)
class Organ:
    id: str
    namn: tuple[str, ...]
    fran: date | None
    till: date | None
    foregangare: tuple[str, ...]
    hor_till: str | None = None
    # Gruppen organet står i på kommunens sida; ett utskott står i sitt organs.
    grupp: str | None = None
    # Första året organets sammanträden får en egen sida (K54).
    sammantradessidor: int | None = None


def organ_av(post: dict) -> Organ:
    var = f"organ {post.get('id')!r}"
    schema.kontrollera_falt(post, ORGANFALT, var)
    namn = namn_av(post, var)
    return Organ(
        id=schema.katalognamn(schema.varde(post, "id", str, var), var),
        namn=namn,
        fran=schema.valfritt(post, "fran", date, var),
        till=schema.valfritt(post, "till", date, var),
        foregangare=schema.textlista(post, "foregangare", var),
        hor_till=schema.valfritt(post, "hor_till", str, var),
        grupp=schema.valfritt(post, "grupp", str, var),
        sammantradessidor=schema.valfritt(post, "sammantradessidor", int, var),
    )


def namn_av(post: dict, var: str) -> tuple[str, ...]:
    namn = schema.textlista(post, "namn", var)
    if not namn:
        raise Konfigurationsfel(f"{var}: organet har inget namn")
    return namn


def kontrollera_organ(organ: tuple[Organ, ...]) -> None:
    kontrollera_hanvisningar(organ)
    for a, b in combinations(organ, 2):
        if delar_namn(a, b) and overlappar(a, b):
            raise Konfigurationsfel(
                f"organ {a.id!r} och {b.id!r}: samma namn samtidigt"
            )


def kontrollera_hanvisningar(organ: tuple[Organ, ...]) -> None:
    id_ = [o.id for o in organ]
    for o in organ:
        if id_.count(o.id) > 1:
            raise Konfigurationsfel(f"organ {o.id!r}: två organ har samma id")
        kontrollera_hanvisning(o, id_)


def kontrollera_hanvisning(o: Organ, id_: list[str]) -> None:
    saknade = [f for f in o.foregangare if f not in id_]
    if saknade:
        raise Konfigurationsfel(
            f"organ {o.id!r}: föregångaren {saknade[0]!r} finns inte"
        )
    if o.hor_till is not None and o.hor_till not in id_:
        raise Konfigurationsfel(f"organ {o.id!r}: hor_till {o.hor_till!r} finns inte")


# Med grupper har varje organ som inte är utskott en av dem; ett utskott
# står i sitt organs grupp och har ingen egen.
def kontrollera_grupper(organ: tuple[Organ, ...], grupper: tuple[str, ...]) -> None:
    for o in organ:
        ska_ha = bool(grupper) and not o.hor_till
        if (o.grupp is not None) != ska_ha or (o.grupp and o.grupp not in grupper):
            raise Konfigurationsfel(f"organ {o.id!r}: grupp {o.grupp!r} passar inte")


def normaliserat(namn: str) -> str:
    return " ".join(namn.casefold().split())


def delar_namn(a: Organ, b: Organ) -> bool:
    return bool({normaliserat(n) for n in a.namn} & {normaliserat(n) for n in b.namn})


def overlappar(a: Organ, b: Organ) -> bool:
    return (a.fran or date.min) <= (b.till or date.max) and (b.fran or date.min) <= (
        a.till or date.max
    )
