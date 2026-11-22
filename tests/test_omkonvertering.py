"""Krav: K8, K9, K13 och K86, ADR-0019 och ADR-0107.
Kod: src/kommunhandlingar/behandla.py och hamta.py."""

from dataclasses import replace

from kommunhandlingar.behandla import Steg2
from kommunhandlingar.hamta import ordna
from tests.test_hamta import Steg2Fall, kandidat


class TestAvstangd(Steg2Fall):
    def test_annan_version_hamtas_inte(self):
        self.klient.filer["u1"] = "kort.pdf"
        self.kor(kandidat("s:1", "u1"), version="kommunhandlingar 0.1.0")
        self.assertEqual(self.kor(kandidat("s:1", "u1")), ["oförändrad"])
        self.assertEqual(self.klient.anrop, ["u1"])
        lista = [kandidat("s:1", "u1"), kandidat("s:2", "u2", "bilaga")]
        self.assertEqual(ordna(self.steg(lista), lista), lista)


class TestOmkonvertering(Steg2Fall):
    def steg(self, kandidater, version: str = "kommunhandlingar 0.2.0") -> Steg2:
        return replace(super().steg(kandidater, version), omkonvertera=True)

    def test_annan_version_konverteras_om(self):
        self.klient.filer["u1"] = "kort.pdf"
        self.kor(kandidat("s:1", "u1"), version="kommunhandlingar 0.1.0")
        self.assertEqual(self.kor(kandidat("s:1", "u1")), ["konverterad om"])
        self.assertEqual(self.klient.anrop, ["u1", "u1"])
        self.assertTrue(self.falt()["pipeline"].startswith("kommunhandlingar 0.2.0 /"))
        self.assertEqual(self.falt()["figurer"], "[4]")
        self.assertEqual(self.kor(kandidat("s:1", "u1")), ["oförändrad"])

    def test_annan_version_som_inte_gar_att_hamta_star_kvar(self):
        self.klient.filer["u1"] = "kort.pdf"
        self.kor(kandidat("s:1", "u1"), version="kommunhandlingar 0.1.0")
        fore = self.md().read_text()
        self.klient.filer["u1"] = "fel:http-404"
        self.assertEqual(
            self.kor(kandidat("s:1", "u1")),
            ["ej hämtad (http-404), fullständig .md orörd"],
        )
        self.assertEqual(self.md().read_text(), fore)

    def test_annan_version_under_ny_adress_konverteras_om(self):
        self.klient.filer |= {"u1": "kort.pdf", "u3": "kort.pdf"}
        self.kor(kandidat("s:1", "u1"), version="kommunhandlingar 0.1.0")
        self.assertEqual(self.kor(kandidat("s:1", "u3")), ["konverterad om"])
        falt = self.falt()
        self.assertEqual(falt["kalla_url"], "u3")
        self.assertTrue(falt["pipeline"].startswith("kommunhandlingar 0.2.0 /"))

    def test_annan_version_och_annat_innehall_blir_ny_version(self):
        self.klient.filer["u1"] = "kort.pdf"
        self.kor(kandidat("s:1", "u1"), version="kommunhandlingar 0.1.0")
        fore = self.falt()["sha256"]
        self.klient.filer["u1"] = "kort-begransad.pdf"
        self.assertEqual(self.kor(kandidat("s:1", "u1")), ["konverterad"])
        self.assertNotEqual(self.falt()["sha256"], fore)

    def test_omkonverteringen_tas_sist(self):
        gamla = [kandidat("s:1", "u1"), kandidat("s:3", "u3", "kallelse")]
        self.klient.filer |= {"u1": "kort.pdf", "u3": "kort.pdf"}
        self.kor(*gamla, version="kommunhandlingar 0.1.0")
        ny = kandidat("s:2", "u2", "bilaga")
        lista = [*gamla, ny]
        self.assertEqual(ordna(self.steg(lista), lista), [ny, *gamla])
        nuvarande = self.steg(lista, "kommunhandlingar 0.1.0")
        self.assertEqual(ordna(nuvarande, lista), lista)
        flyttad = [kandidat("s:1", "u9"), ny]
        self.assertEqual(ordna(self.steg(flyttad), flyttad), flyttad)

    def test_ej_hamtad_flyttas_inte_sist(self):
        self.klient.filer["u1"] = "fel:http-404"
        self.kor(kandidat("s:1", "u1"), version="kommunhandlingar 0.1.0")
        lista = [kandidat("s:1", "u1"), kandidat("s:2", "u2", "bilaga")]
        self.assertEqual(ordna(self.steg(lista), lista), lista)


class TestVersionenBerorDokumentet(Steg2Fall):
    """K86: bara det som en senare version kan ändra konverteras om."""

    TABELL = {(0, 1, 0): frozenset({"alla"}), (0, 2, 0): frozenset({"ocr"})}

    def steg(self, kandidater, version: str = "kommunhandlingar 0.2.0") -> Steg2:
        steg = super().steg(kandidater, version)
        return replace(steg, omkonvertera=True, andringar=self.TABELL)

    def gammal(self, *ersattningar: tuple[str, str]):
        self.klient.filer["u1"] = "kort.pdf"
        self.kor(kandidat("s:1", "u1"), version="kommunhandlingar 0.1.0")
        text = self.md().read_text()
        for fore, efter in ersattningar:
            text = text.replace(fore, efter, 1)
        self.md().write_text(text)

    def test_ett_dokument_som_inte_beroras_ar_oforandrat(self):
        self.gammal()
        self.assertEqual(self.kor(kandidat("s:1", "u1")), ["oförändrad"])
        self.assertEqual(self.klient.anrop, ["u1"])
        self.assertTrue(self.falt()["pipeline"].startswith("kommunhandlingar 0.1.0 /"))
        lista = [kandidat("s:1", "u1"), kandidat("s:2", "u2", "bilaga")]
        self.assertEqual(ordna(self.steg(lista), lista), lista)

    def test_ett_dokument_som_beroras_konverteras_om(self):
        self.gammal(("[ok, ok, tabell-osaker, ok]", "[ok, ocr, tabell-osaker, ok]"))
        self.assertEqual(self.kor(kandidat("s:1", "u1")), ["konverterad om"])
        self.assertTrue(self.falt()["pipeline"].startswith("kommunhandlingar 0.2.0 /"))

    def test_full_konverteras_om_nar_versionen_beror_det(self):
        self.gammal(
            ("kvalitet: text-utan-tabeller", "kvalitet: full"),
            ("[ok, ok, tabell-osaker, ok]", "[ok, ocr, ok, ok]"),
        )
        self.assertEqual(self.kor(kandidat("s:1", "u1")), ["konverterad om"])

    def test_granskat_berors_aldrig(self):
        self.gammal(
            ("[ok, ok, tabell-osaker, ok]", "[ok, ocr, tabell-osaker, ok]"),
            ("granskad: null", "granskad: 2026-10-22"),
        )
        self.assertEqual(self.kor(kandidat("s:1", "u1")), ["oförändrad"])
