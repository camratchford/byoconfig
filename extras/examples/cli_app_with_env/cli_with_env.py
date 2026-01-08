import argparse
from os import environ

from byo_config import Config


def print_config(config):
    print(f"{config} = {config.get()}\n")


def main():
    parser = argparse.ArgumentParser(
        prog="example-cli-app", description="A demonstration of the BYOConfig library"
    )

    parser.add_argument(
        "-c", "--config", type=str, help="The path to the configuration file"
    )

    args = parser.parse_args()

    config = Config(
        var_source_name="example-cli-app",
        precedence=1,
        source_file_path=args.config,
        env_prefix="EXAMPLE_CLI_APP_",
    )

    print_config(config)


if __name__ == "__main__":
    # Adds a new key 'test' to the config object
    environ.update({"EXAMPLE_CLI_APP_test": "test"})

    # Overwrites the value of the key 'from_env' in the config object that was set in the example.yml file
    environ.update({"EXAMPLE_CLI_APP_from_env": "other value"})

    main()
