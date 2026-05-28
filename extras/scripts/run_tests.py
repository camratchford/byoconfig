from .common import (
    check_package_installed_as_editable,
    run,
)


def cli():
    check_package_installed_as_editable()
    process = run("pytest -v ./tests")

    if process.returncode == 0:
        print("::info:: Tests passed")
        return

    print(process.stderr, process.stdout)
    exit(process.returncode)


if __name__ == "__main__":
    cli()
