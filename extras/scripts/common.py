import subprocess
import site
from pathlib import Path
from sys import exit
import re
from packaging.version import Version

this_directory = Path(__file__).parent
project_root = this_directory.parent.parent
pyproject_dot_toml = project_root / "pyproject.toml"
package_name = "byoconfig"


def run(cmd):
    print(f"Running: {cmd}")
    return subprocess.run(
        cmd,
        shell=True,
        text=True,
        cwd=project_root,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        check=False,
    )


def package_installed_as_editable(package: str = package_name) -> bool:
    for path in site.getsitepackages() + [site.getusersitepackages()]:
        if not Path(path).exists():
            continue
        editable_pkgs = [
            p.name for p in Path(path).iterdir() if p.is_file() and p.suffix == ".pth"
        ]
        for pkg in editable_pkgs:
            if package in pkg:
                return True
    return False


class ScriptEnvironmentError(Exception):
    def __init__(self, package, name):
        message = (
            f"PyPi package '{package}' is not installed with '-e' option.\n"
            f"This is required to give relative paths to {name}."
            ""
        )
        print(message)
        super().__init__(message)
        exit(1)


class ScripCLIError(Exception):
    def __init__(self, process: subprocess.CompletedProcess):
        error_message = "\n".join((process.stdout, process.stderr))
        message = (
            f"CLI command {process.args} completed with error code {process.returncode}\n"
            f"::error:: {error_message}"
        )
        print(message)
        super().__init__(message)
        exit(1)


def check_subprocess_for_errors(process: subprocess.CompletedProcess):
    if process.returncode != 0:
        raise ScripCLIError(process)


def get_current_branch():
    return subprocess.run(
        "git rev-parse --abbrev-ref HEAD",
        text=True,
        cwd=project_root,
        capture_output=True,
        check=False,
    ).stdout.strip()


def check_branch(target_branch: str = "main"):
    current_branch = get_current_branch()
    if current_branch != target_branch:
        print(
            f"::error:: You must be on the main branch to release. Current branch is '{current_branch}'."
        )
        exit(1)


def get_current_version() -> Version:
    content = pyproject_dot_toml.read_text()
    match = re.search(r'^version\s*=\s*["\'](.+?)["\']', content, re.MULTILINE)
    if not match:
        exit("Version not found in pyproject.toml")
    return Version(match.group(1))
