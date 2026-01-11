import os
import shutil
from pathlib import Path

from platformdirs import user_cache_path, user_config_path, user_data_path

# Future-proofing: pyfakefs will be used in TestRootEnvironment
# import pyfakefs.fake_filesystem_unittest as fake_fs


class TestHomeEnvironment:
    """
    Manages a physical test directory on the real filesystem.

    This class provides a sandbox by redirecting the user's HOME and
    related environment variables to a specific test directory. This
    isolates the developer's actual system from side effects during
    test execution.
    """

    def __init__(self, base_dir: Path):
        """
        Initialize the environment paths.

        :param base_dir: Path to the directory acting as the test anchor.
        """
        self._base_dir = base_dir.resolve()
        self._input_dir = self._base_dir / "testinput"
        self._output_dir = self._base_dir / "testoutput"
        self._orig_cwd = Path.cwd()
        self._orig_env = {}
        self._do_not_clean=False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(base_dir={self._base_dir!r})"

    @property
    def base_dir(self) -> Path:
        """
        The root of the test environment **(ro)**.
        """
        return self._base_dir

    @property
    def HOME(self) -> Path:
        """
        Alias for base_dir to provide intuitive access to the simulated HOME **(ro)**.
        """
        return self.base_dir

    @property
    def input_dir(self) -> Path:
        """
        Read-only directory containing Git-tracked test files **(ro)**.
        """
        return self._input_dir

    @property
    def output_dir(self) -> Path:
        """
        Writable directory for test execution **(ro)**.
        """
        return self._output_dir

    @property
    def input_readonly(self) -> bool:
        """
        Control the write permissions of the testinput directory **(rw)**.

        :param value: Set to True to make the directory read-only, False for writable (Setter).
        """
        return not os.access(self.input_dir, os.W_OK)

    @input_readonly.setter
    def input_readonly(self, value: bool) -> None:
        """
        Control the write permissions of the testinput directory **(rw)**.

        :param value: Set to True to make the directory read-only, False for writable.
        :raises OSError: If the file mode cannot be changed (Setter).
        """
        mode = 0o555 if value else 0o755
        os.chmod(self.input_dir, mode)

    @property
    def do_not_clean(self) -> bool:
        """
        Toggle the automatic cleaning of the test directory (**rw**).

        :param value: The boolean state to enable or disable cleaning.
        :returns: The current state of the cleaning lock.
        """
        return self._do_not_clean

    @do_not_clean.setter
    def do_not_clean(self, value: bool) -> None:
        """
        Toggle the automatic cleaning of the test directory (**rw**).

        :param value: The boolean state to enable or disable cleaning.
        :returns: The current state of the cleaning lock.
        """
        self._do_not_clean = bool(value)

    def setup(self, clean_output: bool = True) -> None:
        """
        Prepare the environment, redirect HOME, and switch to output_dir.

        :param clean_output: If True, existing output files are deleted.
        :raises OSError: If directories cannot be created or deleted.
        """
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.input_dir.mkdir(parents=True, exist_ok=True)

        if clean_output and self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        env_to_redirect = ["HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA"]
        env_to_neutralize = [
            "XDG_CONFIG_HOME",
            "XDG_DATA_HOME",
            "XDG_CACHE_HOME",
            "XDG_RUNTIME_DIR",
            "XDG_STATE_HOME",
        ]

        for var in env_to_redirect + env_to_neutralize:
            if var in os.environ:
                self._orig_env[var] = os.environ[var]

            if var in env_to_redirect:
                os.environ[var] = str(self.base_dir)
            else:
                if var in os.environ:
                    del os.environ[var]

        os.chdir(self.output_dir)

    def _copy_to_user_dir(
        self, app_name: str, source_name: str, target_name: str, get_path_func
    ) -> Path:
        """
        Internal helper for deploying files from testinput to user directories.

        :param app_name: Name of the application.
        :param source_name: Filename inside input_dir.
        :param target_name: Optional new name at the destination.
        :param get_path_func: Function to retrieve the target platform path.
        :raises FileNotFoundError: If the source file is missing.
        :raises OSError: If the copy operation fails.
        :returns: The path to the newly created file.
        """
        source_path = self.input_dir / source_name
        if not source_path.exists():
            raise FileNotFoundError(f"Source file {source_name} not found in {self.input_dir}")

        target_dir = get_path_func(app_name)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / (target_name or source_name)

        shutil.copy2(source_path, target_path)
        return target_path

    def copy2config(self, app_name: str, source_name: str, target_name: str = None) -> Path:
        """
        Copy a file from testinput to the OS-specific user config directory.

        :param app_name: Name of the application.
        :param source_name: Filename inside input_dir.
        :param target_name: Optional new name at the destination.
        :raises FileNotFoundError: If the source file is missing.
        :returns: The path to the newly created configuration file.
        """
        return self._copy_to_user_dir(app_name, source_name, target_name, user_config_path)

    def copy2data(self, app_name: str, source_name: str, target_name: str = None) -> Path:
        """
        Copy a file from testinput to the OS-specific user data directory.

        :param app_name: Name of the application.
        :param source_name: Filename inside input_dir.
        :param target_name: Optional new name at the destination.
        :raises FileNotFoundError: If the source file is missing.
        :returns: The path to the newly created data file.
        """
        return self._copy_to_user_dir(app_name, source_name, target_name, user_data_path)

    def copy2cache(self, app_name: str, source_name: str, target_name: str = None) -> Path:
        """
        Copy a file from testinput to the OS-specific user cache directory.

        :param app_name: Name of the application.
        :param source_name: Filename inside input_dir.
        :param target_name: Optional new name at the destination.
        :raises FileNotFoundError: If the source file is missing.
        :returns: The path to the newly created cache file.
        """
        return self._copy_to_user_dir(app_name, source_name, target_name, user_cache_path)

    def copy2cwd(self, source_name: str, target_name: str = None) -> Path:
        """
        Copy a file from testinput directly to the current working directory.

        As setup() changes the CWD to output_dir, this method places files
        directly into the active test sandbox.

        :param source_name: Filename inside input_dir.
        :param target_name: Optional new name in the current directory.
        :raises FileNotFoundError: If the source file is missing.
        :returns: The path to the newly created file in the CWD.
        """
        source_path = self.input_dir / source_name
        if not source_path.exists():
            raise FileNotFoundError(f"Source file {source_name} not found in {self.input_dir}")

        target_path = Path.cwd() / (target_name or source_name)
        shutil.copy2(source_path, target_path)
        return target_path

    def teardown(self) -> None:
        """
        Restore the original environment variables and working directory.
        """
        os.chdir(self._orig_cwd)
        for var, value in self._orig_env.items():
            os.environ[var] = value

    def clean_home(self) -> None:
        """
        Remove all files and directories from the simulated HOME except testinput.

        This method cleans the sandbox while preserving the static input files
        required for further tests. The cleaning process can be suppressed by 
        setting the property **do_not_clean** to True. If the property is 
        active, calling this method will have no effect on the file system.
        """
        if self.do_not_clean:
            return

        for item in self.base_dir.iterdir():
            if item == self.input_dir:
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()


class TestRootEnvironment:
    """
    Placeholder for future pyfakefs-based system simulation.
    """

    def __init__(self):
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


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
    dt_file = str(testfilesbasedir / "get_started_ftw_testinfra.rst")
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
