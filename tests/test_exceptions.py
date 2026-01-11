
from fitzzftw.patch.ftw_patch import FtwPatchError, PatchParseError

#FehlerKlasse1, FehlerKlasse2

class TestFtwPatchError:
    def test_repr(self):
        """Deckt Zeile 74 ab (repr)."""
        msg = "Fehlermeldung 1"
        exc = FtwPatchError(msg)
        assert msg in repr(exc)
        assert "FtwPatchError" in repr(exc)

class TestPatchParseError:
    def test_repr(self):
        """Deckt Zeile 97 ab (repr)."""
        msg = "Fehlermeldung 2"
        exc = PatchParseError(msg)
        assert msg in repr(exc)
        assert "PatchParseError" in repr(exc)
