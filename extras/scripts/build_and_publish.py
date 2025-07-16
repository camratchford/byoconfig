from pathlib import Path
from argparse import ArgumentParser
import shutil

import build
import twine.commands.upload
from twine.settings import Settings

from byoconfig.scripts.common import (
    project_root,
    package_installed_as_editable,
    ScriptEnvironmentError,
    check_branch,
    package_name,
)

default_sdist_path = project_root / "sdist"


def build_python_package(sdist_dir: Path):
    this_file = Path(__file__).resolve()
    this_dir = this_file.parent
    project_root = this_dir.parent.parent

    if sdist_dir.exists():
        shutil.rmtree(sdist_dir)
    sdist_dir.mkdir(parents=True, exist_ok=True)

    builder = build.ProjectBuilder(project_root)
    builder.build("wheel", output_directory=str(sdist_dir.absolute()))
    builder.build("sdist", output_directory=str(sdist_dir.absolute()))

    dist_files = [str(p) for p in sdist_dir.iterdir()]

    return dist_files


def publish(dist_files: list[str]):
    settings = Settings(
        verbose=True,
        repository_name="pypi",
    )
    twine.commands.upload.upload(settings, dist_files)


def main(sdist_dir: Path, publish_to_pypi: bool):
    dist_files = build_python_package(sdist_dir)
    if publish_to_pypi:
        check_branch()
        publish(dist_files)


def cli():
    parser = ArgumentParser()
    parser.add_argument(
        "--sdist-dir",
        type=Path,
        default=default_sdist_path,
        help="Where to put the sdist files",
    )
    parser.add_argument(
        "--publish", action="store_true", help="Publish to PyPi after build"
    )
    args = parser.parse_args()
    if not package_installed_as_editable():
        raise ScriptEnvironmentError(package_name, __name__)
    main(args.sdist_dir, publish_to_pypi=args.publish)


if __name__ == "__main__":
    cli()
