import sys
import typing

import pytest

from fitzzftw.patch.future_314_ge import FtwProtocolWrap


@pytest.mark.skipif(sys.version_info < (3, 14), reason="Nur für 3.14+ (annotationlib)")
def test_coverage_gap_any_only():
    """
    Chirurgischer Test für Zeile 87.
    Umgeht die instabile Introspektion lokaler Klassen-Dunder.
    """
    # Instanz ohne Argument = kein automatisches set_new_protocol()
    wrapper = FtwProtocolWrap()

    # Wir testen die reine String-Konvertierung von Any
    # Das nutzt die stabilen Dunder-Checks innerhalb der Methode
    assert wrapper._get_type_str(typing.Any) == "Any"
