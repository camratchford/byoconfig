from byoconfig.scripts.common import (
    run,
    package_installed_as_editable,
    ScriptEnvironmentError,
    package_name,
)


def cli():
    if not package_installed_as_editable():
        raise ScriptEnvironmentError(package_name, __name__)

    run("pytest ./tests")


if __name__ == "__main__":
    cli()
