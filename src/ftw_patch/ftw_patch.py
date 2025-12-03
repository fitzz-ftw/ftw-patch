"""
FTW Patch
===============================

| File: ftw_patch/ftw_patch.py
| Author: Fitzz TeXnik Welt
| Email: FitzzTeXnikWelt@t-online.de

Ein Unicode resistenter Ersatz für patch.


"""
from argparse import ArgumentParser


def cli_parse_ftw_patch()->ArgumentParser:
    """
    Creates the parser for ftwpatch commandline interface.

    :return: Commandline interface parser with all options ready to
            parse ''sys.args''.
    :rtype: ArgumentParser
    """
    parser = ArgumentParser(prog="ftwpatch")
    ''' Add your code here '''
    return parser





def prog_ftw_patch(): # pyright: ignore[reportUndefinedVariable]
    """
    Function that represents the program defined
    in pyproject.toml under [project.scripts].
    """
    print("Hello ftwpatch")



if __name__ == "__main__":
    from doctest import testfile, FAIL_FAST
    from pathlib import Path
    be_verbose=False
    be_verbose=True
    option_flags= 0
    option_flags= FAIL_FAST
    testfilesbasedir = Path("../../docs/source/devel")
    test_sum = 0
    doctestresult = testfile(
        str(testfilesbasedir / "get_started_ftw_patch.rst"),
        verbose=be_verbose,
        optionflags=option_flags,
    )
    test_sum += doctestresult.attempted
    if doctestresult.failed:
        print(f"Total tests run: {test_sum}" )
        exit(1)
