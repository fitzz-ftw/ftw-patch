import sys

import pytest

from fitzzftw.patch.legacy_311 import sig2str


@pytest.mark.skipif(sys.version_info >= (3, 12), reason="Legacy 3.11 Support Check")
def test_sig2str_exception_fallback():
    """
    Triggert den Exception-Block in sig2str (legacy_311.py, Zeilen 51-52).
    Ein Integer hat keine __annotations__, was den AttributeError wirft.
    """
    # Ein int-Objekt hat keine __annotations__, der try-Block stirbt sofort.
    result = sig2str(42) # type: ignore

    # Der Catch-all muss den definierten Fallback-String liefern.
    assert result == "(<not availible>)"
