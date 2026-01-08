import argparse

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
    main()
