"""Kod: src/kommunhandlingar/webbplats/inbaddning.py."""

import unittest
from unittest import mock

from kommunhandlingar.webbplats import inbaddning
from kommunhandlingar.webbplats.inbaddning import KATALOG, las, skript, stil


class TestInbaddning(unittest.TestCase):
    def test_stilarna_star_i_en_tagg(self):
        mal, spar = las("mal.css"), las("spar.css")
        self.assertEqual(stil("mal.css", "spar.css"), f"<style>{mal}{spar}</style>")

    def test_varje_skript_far_sin_tagg(self):
        mal, perspektiv = las("mal.js"), las("perspektiv.js")
        self.assertEqual(
            skript("mal.js", "perspektiv.js"),
            f"<script>{mal}</script><script>{perspektiv}</script>",
        )

    def test_filen_ar_den_bredvid_koden(self):
        text = (KATALOG / "kalender.css").read_text(encoding="utf-8")
        self.assertEqual(las("kalender.css"), text)

    def test_en_fil_lases_en_gang(self):
        inbaddning.las.cache_clear()
        with mock.patch.object(
            type(KATALOG), "read_text", autospec=True, return_value="x"
        ) as lasning:
            stil("mote.css")
            stil("mote.css")
        inbaddning.las.cache_clear()
        self.assertEqual(lasning.call_count, 1)


if __name__ == "__main__":
    unittest.main()
