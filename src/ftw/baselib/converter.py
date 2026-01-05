def str2bool(value: str | bool) -> bool:
    """
    Convert a string or boolean to a real boolean value.

    This function is designed for CLI and configuration parsing. It
    interprets 'true', 'yes', '1', 'on' as True and their opposites as False.

    :param value: The value to be converted.
    :raises ValueError: If the value cannot be mapped to a boolean.
    :returns: The resulting boolean value.
    """
    if isinstance(value, bool):
        return value

    normalized = str(value).lower().strip()
    
    mapping = {
        'true': True, 'yes': True, 't': True, 'y': True, '1': True, 'on': True,
        'false': False, 'no': False, 'f': False, 'n': False, '0': False, 'off': False
    }

    if normalized in mapping:
        return mapping[normalized]

    raise ValueError(f"Cannot convert '{value}' to boolean.")


if __name__ == "__main__":  # pragma: no cover
    from doctest import testfile, FAIL_FAST  # noqa: I001
    from pathlib import Path
    import sys

    # Adds the project's root directory (the module source directory)
    # to the beginning of sys.path.
    project_root = Path(__file__).resolve().parent.parent
    print(project_root)
    sys.path.insert(0, str(project_root))
    be_verbose = False
    be_verbose = True
    option_flags = 0
    option_flags = FAIL_FAST
    testfilesbasedir = Path("../../../doc/source/devel")
    test_sum = 0
    test_failed = 0
    dt_file = str(testfilesbasedir / "get_started_ftw_converter.rst")
    # dt_file = str(testfilesbasedir / "temp_test.rst")
    # dt_file = str(testfilesbasedir / "test_parser_fix.rst")
    # dt_file = str(testfilesbasedir / "parser_validation.txt")
    print(dt_file)
    doctestresult = testfile(
        dt_file,
        # "../../doc/source/devel/get_started_ftw_patch.rst",
        optionflags=option_flags,
        verbose=be_verbose,
    )
    test_failed += doctestresult.failed
    test_sum += doctestresult.attempted

    # doctestresult = testfile(
    #     str(testfilesbasedir / "ftw_patch.rst"),
    #     optionflags=option_flags,
    #     verbose=be_verbose,
    # )
    # test_failed += doctestresult.failed
    # test_sum += doctestresult.failed

    if test_failed == 0:
        print(f"DocTests passed without errors, {test_sum} tests.")
    else:
        print(f"DocTests failed: {test_failed} tests.")
