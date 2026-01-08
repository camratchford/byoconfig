from pathlib import Path
from byo_config import Config


def print_config(config):
    print(f"{config} = {config.get()}\n")


def main():
    this_dir = Path(__file__).parent

    json_config = Config(
        var_source_name="json-config",
        source_file_path=str(this_dir / "same_as.json"),
    )

    toml_config = Config(
        var_source_name="toml-config",
        source_file_path=str(this_dir / "same_as.toml"),
    )

    yaml_config = Config(
        var_source_name="yaml-config",
        source_file_path=str(this_dir / "same_as.yaml"),
    )

    print_config(json_config)
    print_config(toml_config)
    print_config(yaml_config)

    if json_config.get() == toml_config.get() == yaml_config.get():
        print("All configs are the same")


if __name__ == "__main__":
    main()
