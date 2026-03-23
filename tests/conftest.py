import sys


def pytest_ignore_collect(collection_path, config):
    """
    Verhindert, dass inkompatible Dateien überhaupt geladen werden.
    """
    path_str = str(collection_path)
    v = sys.version_info

    # Logik für 3.14+
    if v >= (3, 14):
        if "legacy_311" in path_str or "current_312_313" in path_str:
            return True

    # Logik für < 3.14
    if v < (3, 14) and "future_314" in path_str:
        return True

    # Logik für >= 3.12 (Legacy 3.11 ignorieren)
    if v >= (3, 12) and "legacy_311" in path_str:
        return True

    return False
