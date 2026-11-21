"""Krav: K81 i docs/02-KRAV.md. Det som testerna av kommandona delar:
en temporär katalog per test, och kommandots utskrift och slutkod."""

import contextlib
import io
import runpy
import sys
import tempfile
import unittest
import warnings
from pathlib import Path
from unittest import mock


class Katalogfall(unittest.TestCase):
    def setUp(self):
        katalog = tempfile.TemporaryDirectory()
        self.addCleanup(katalog.cleanup)
        self.rot = Path(katalog.name)


def utskrift_av(kommando, *argument) -> str:
    with contextlib.redirect_stdout(io.StringIO()) as utskrift:
        kommando(*argument)
    return utskrift.getvalue()


def kor_modulen(modul: str, *argument: str) -> tuple[object, str]:
    """Slutkoden, eller None, och det som skrevs på standard ut."""
    with (
        warnings.catch_warnings(),
        mock.patch.object(sys, "argv", [modul, *argument]),
        contextlib.redirect_stdout(io.StringIO()) as utskrift,
    ):
        # runpy varnar när modulen redan är importerad.
        warnings.simplefilter("ignore", RuntimeWarning)
        try:
            runpy.run_module(f"kommunhandlingar.{modul}", run_name="__main__")
        except SystemExit as stopp:
            return stopp.code, utskrift.getvalue()
    return None, utskrift.getvalue()
