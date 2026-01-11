
import pytest


def test_ftw_patch_import():
    """Prüft, ob das Paket im Namespace 'ftw' korrekt importiert werden kann."""
    try:
        import fitzzftw.patch
        print(f"\n[OK] fitzzftw.patch erfolgreich importiert aus: {fitzzftw.patch.__file__}")
    except ImportError as e:
        pytest.fail(f"Import fehlgeschlagen: {e}. Prüfe pyproject.toml Namespace-Settings!")

def test_version_generation():
    """Prüft, ob setuptools_scm die Versionsdatei korrekt erzeugt hat."""
    try:
        from fitzzftw.patch._version import version
        print(f"[OK] Version erkannt: {version}")
        assert version != "0.0.0"
    except ImportError:
        pytest.fail("_version.py wurde nicht generiert. Git-Tag vorhanden?")
