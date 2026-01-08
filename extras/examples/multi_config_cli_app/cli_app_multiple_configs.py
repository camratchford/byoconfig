import argparse

from byo_config import Config


def print_config(config):
    print(f"{config} = {config.get()}\n")


def main():
    parser = argparse.ArgumentParser(
        prog="example-cli-app", description="A demonstration of the BYOConfig library"
    )

    parser.add_argument(
        "--config-a", type=str, help="The path to the default configuration file"
    )

    parser.add_argument(
        "--config-b", type=str, help="The path to the more specific configuration file"
    )

    args = parser.parse_args()

    config_a = Config(
        var_source_name="example-a", precedence=1, source_file_path=args.config_a
    )

    config_b = Config(
        var_source_name="example-b",
        precedence=2,  # Higher precedence than config_a
        source_file_path=args.config_b,
    )

    print_config(config_a)
    print_config(config_b)

    # Left-side config values are overwritten by right-side config values
    # Left-side config name and precedence are preserved
    config_a += config_b

    print_config(config_a)


if __name__ == "__main__":
    main()
