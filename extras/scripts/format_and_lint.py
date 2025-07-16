from argparse import ArgumentParser

from byoconfig.scripts.common import (
    project_root,
    run,
    package_installed_as_editable,
    ScriptEnvironmentError,
    check_subprocess_for_errors,
    package_name,
)


def main(directories: list[str], test_mode: bool):
    dir_arg = " ".join(directories)
    check_test_arg, format_test_arg = "", ""
    if test_mode:
        check_test_arg = "--exit-non-zero-on-fix"
        format_test_arg = "--check --exit-non-zero-on-fix"

    check_process = run(f"ruff check --show-fixes --fix {check_test_arg} {dir_arg}")
    format_process = run(f"ruff format {format_test_arg} {dir_arg}")

    if test_mode:
        check_subprocess_for_errors(check_process)
        check_subprocess_for_errors(format_process)


def cli():
    parser = ArgumentParser()
    parser.add_argument(
        "--test",
        action="store_true",
        help="Exits with error if ruff needs to make changes",
    )
    parser.add_argument(
        "--directories",
        nargs="+",
        help="List of directories to format and lint",
        default=["."],
    )
    args = parser.parse_args()
    dir_paths = [project_root / directory for directory in args.directories]
    missing_paths = [d for d in dir_paths if not d.exists()]
    if missing_paths:
        paths_str = " ".join(str(i) for i in missing_paths)
        raise ScriptEnvironmentError(
            f"Some directories are not accessible: {paths_str}. "
            f"Did forget to install this pacakge with 'pip install -e'?"
        )

    if not package_installed_as_editable():
        raise ScriptEnvironmentError(package_name, __name__)

    main(directories=args.directories, test_mode=args.test)


if __name__ == "__main__":
    cli()
