import re
import sys
from packaging.version import Version
import argparse

from github import Github

from byoconfig.scripts.common import (
    run,
    get_current_version,
    pyproject_dot_toml,
    package_name,
    package_installed_as_editable,
    ScriptEnvironmentError,
)


def get_new_version(version: Version, kind: str) -> str:
    if kind == "patch":
        return f"{version.major}.{version.minor}.{version.micro + 1}"
    elif kind == "minor":
        return f"{version.major}.{version.minor + 1}.0"
    elif kind == "major":
        return f"{version.major + 1}.0.0"
    elif kind == "dev":
        return f"{version.major}.{version.minor}.{version.micro + 1}.dev0"
    else:
        sys.exit(f"Invalid bump type: {kind}")


def set_new_version(new_version: str):
    content = pyproject_dot_toml.read_text()
    new_content = re.sub(
        r'(^version\s*=\s*["\'])(.+?)(["\'])',
        rf'version = "{new_version}"',
        content,
        flags=re.MULTILINE,
    )
    pyproject_dot_toml.write_text(new_content)


def git_tag(version: str):
    run(f"git add {pyproject_dot_toml}")
    run(f'git commit -m "Release {version}"')
    run(f"git tag v{version}")
    run("git push")
    run(f"git push origin v{version}")


def main(
    patch_release: bool,
    minor_release: bool,
    major_release: bool,
    manual_version: bool,
    dry_run: bool = False,
) -> None:
    kind = (
        "patch"
        if patch_release
        else "minor"
        if minor_release
        else "major"
        if major_release
        else "dev"
    )

    current_version = get_current_version()
    new_version = current_version
    if not manual_version:
        new_version = get_new_version(current_version, kind)

    print(f"Bumping version: {current_version} → {new_version}")
    if not dry_run:
        set_new_version(new_version)
        git_tag(new_version)


def cli():
    parser = argparse.ArgumentParser(description="Bump version and create release.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--patch", action="store_true", help="Bump patch version (x.y.z → x.y.z+1)"
    )
    group.add_argument(
        "--minor", action="store_true", help="Bump minor version (x.y.z → x.y+1.0)"
    )
    group.add_argument(
        "--major", action="store_true", help="Bump major version (x.y.z → x+1.0.0)"
    )
    group.add_argument(
        "--dev",
        action="store_true",
        help="Bump to next patch with dev suffix (x.y.z → x.y.z+1.dev0)",
    )
    group.add_argument(
        "--manual-version",
        action="store_true",
        help="Don't auto-increment based on release type",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show log messages, do not modify version in any way",
    )

    args = parser.parse_args()

    if not package_installed_as_editable():
        raise ScriptEnvironmentError(package_name, __name__)

    main(
        patch_release=args.patch,
        minor_release=args.minor,
        major_release=args.major,
        dry_run=args.dry_run,
        manual_version=args.manual_version,
    )


if __name__ == "__main__":
    cli()
