from byoconfig.scripts.common import (
    run,
    package_installed_as_editable,
    ScriptEnvironmentError,
    package_name,
)


def cli():
    if not package_installed_as_editable():
        raise ScriptEnvironmentError(package_name, __name__)

    process = run("pytest ./tests")
    if process.returncode == 0:
        print("::info:: Tests passed")


if __name__ == "__main__":
    cli()
