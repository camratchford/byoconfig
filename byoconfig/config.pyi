from typing import Optional, Any, Type
from pathlib import Path

from sources.base import BaseVariableSource
from sources.file import FileVariableSource, FileTypes
from sources.environment import EnvVariableSource
from sources.aws_secrets_manager import SecretsManagerVariableSource

class Config(EnvVariableSource, FileVariableSource, SecretsManagerVariableSource):
    """
    A versatile config object that can load data from multiple source types, optionally storing them as instance attributes.
    """
    def __init__(
        self,
        config_data: Optional[dict[str, Any]] = None,
        config_name: Optional[str] = "Config",
        config_assign_attrs: Optional[bool] = False,
        env_selected_keys: list[str] = None,
        env_prefix: Optional[str] = None,
        env_trim_prefix: bool = True,
        file_path: Optional[str] = None,
        file_forced_type: Optional[FileTypes] = None,
        aws_secret_name: Optional[str] = "",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        aws_region: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize a Config object from sources containing configuration data in key/value pairs.

        Load order: (Load methods defining keys previously defined by other load methods will overwrite the existing data.)
            1. Files via the `file_path` parameter
            2. Environment Variables via the `env_prefix` or `env_selected_keys` parameters
            3. AWS Secrets Manager secrets via the `aws_secret_name` parameter
            4. Data contained in the `config_data` parameter
            5. Data provided via any extra `kwargs` you provide

        To load keys in a specific order, invoke the desired '.load_' methods after initializing your config instance.

        Args:
            config_data (dict[str, Any]):
                key/value pairs to store as additional configuration data.

            config_name (str):
                The name of your Config instance. Useful for debugging / logging.

            config_assign_attrs (bool):
                If True, instance attributes will be created for top-level configuration data keys.
                Be careful not to overwrite method names.
                Ex. ```
                    config = Config(config_assign_attrs=True, var_1=1, var_2=2)
                    print(config.var_1)
                    # > 1
                    config.var_2 += config.var_1
                    print(config.var_2)
                    # > 3
                ```

            env_selected_keys (list[str]):
                A list of environment variables you want to store as configuration data.

            env_prefix (str):
                The configuration data will be loaded from the environment variables with this prefix.
                Use the `"*"` wildcard if you want to load all environment variables as configuration data.

            env_trim_prefix (Optional[bool]):
                If False, remove the prefix from the stored configuration data keys.
                If True, don't remove the prefix from the stored configuration data keys.

            file_path (str):
                The path to the source file (YAML, JSON, or TOML) containing your configuration data.

            file_forced_type (FileTypes: ['YAML', 'JSON', 'TOML'] ):
                The file type of the source file, if you don't want to use the file's extension.

            aws_secret_name (str):
                The name of the secret stored in AWS Secrets Manager.

            aws_access_key_id (str):
                The access key for your AWS account.
                See https://boto3.amazonaws.com/v1/documentation/api/1.9.46/guide/configuration.html#configuring-credentials for alternative methods of authentication.

            aws_secret_access_key (str):
                The secret key for your AWS account.
                See https://boto3.amazonaws.com/v1/documentation/api/1.9.46/guide/configuration.html#configuring-credentials for alternative methods of authentication.

            aws_session_token (str):
                The session key for your AWS account. This is only needed when you are using temporary credentials.
                Such as retrieving temporary credentials using AWS STS. Ex. `sts.get_session_token()`.
                See https://boto3.amazonaws.com/v1/documentation/api/1.9.46/guide/configuration.html#configuring-credentials for alternative methods of authentication.

            aws_region (str):
                The AWS region to use, e.g. `us-west-1`, `us-west-2`, etc.

            **kwargs:
                key:str / value:any pairs to store as additional configuration data.

        """
        ...

    def include(self, plugin_class: Type[BaseVariableSource], **kwargs):
        """
        Include a plugin class in the config object.

        Args:
            plugin_class (Type[BaseVariableSource]):
                The plugin class to include in the config object. Plugin class must inherit BaseVariableSource.

            **kwargs:
                Keyword arguments to pass to the plugin class's __init__ method.
        """
        ...

    def load_from_file(self, path: str = None, forced_type: FileTypes = None):
        """
        Loads configuration data from the source file, overwriting keys that exist in both with the data from source_file.

        Args:
            path (str):
                The path to the source file. Format is implied by the file's suffix/extension.
                Options are: 'YAML (.yml, .yaml), TOML (.toml), JSON (.json)'

            forced_type (FileTypes: ['YAML', 'JSON', 'TOML'] ):
                The file type of the source file, if you can't (or don't want to) use the file's extension.
        """
        ...

    def dump_to_file(self, destination_path: Path, forced_type: FileTypes = None):
        """
        Dumps configuration data to a file.

        Args:
            destination_path (Path):
                The path to the destination file. Format is implied by the file's suffix/extension.
                Options are: 'YAML (.yml, .yaml), TOML (.toml), JSON (.json)'

            forced_type (FileTypes):
                The file type of the source file, if you can't (or don't want to) use the file's suffix/extension.
        """
        ...

    def load_from_environment(
        self,
        selected_keys: list[str] = None,
        prefix: Optional[str] = None,
        trim_prefix: bool = True,
    ):
        """
        Loads environment variables as configuration data.

        Args:
            selected_keys (list[str]):
                A list of environment variables you want to store as configuration data.

            prefix (Optional[str]):
                A string containing the substring of characters that prefix a set of environment variable keys.

            trim_prefix (Optional[bool]):
                If False, remove the prefix from the stored configuration data keys.
                If True, don't remove the prefix from the stored configuration data keys.
        """
        ...

    def dump_to_environment(
        self,
        selected_keys: list[str] = None,
        use_uppercase: bool = True,
        with_prefix: str = None,
    ):
        """
        Dumps configuration data as environment variables.

        Args:
            selected_keys (list[str]):
                A list of configuration data keys to dump as environment variables.
                None implies that you wish to dump all configuration data keys.

            use_uppercase (bool):
                If False, each created/modified environment variable will have their names converted to uppercase

            with_prefix (str):
                If provided, each created/modified environment variables will have their name prepended with the value
                if with_prefix.
        """
        ...

    def load_from_secrets_manager(
        self,
        aws_secret_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        aws_region: Optional[str] = None,
        **kwargs,
    ):
        """
        Loads JSON encoded secrets from AWS Secrets Manager.

        Args:
            aws_secret_name (str):
                The name of the secret stored in AWS Secrets Manager.

            aws_access_key_id (str):
                The access key for your AWS account.
                See https://boto3.amazonaws.com/v1/documentation/api/1.9.46/guide/configuration.html#configuring-credentials for alternative methods of authentication.

            aws_secret_access_key (str):
                The secret key for your AWS account.
                See https://boto3.amazonaws.com/v1/documentation/api/1.9.46/guide/configuration.html#configuring-credentials for alternative methods of authentication.

            aws_session_token (str):
                The session key for your AWS account. This is only needed when you are using temporary credentials.
                Such as retrieving temporary credentials using AWS STS. Ex. `sts.get_session_token()`.
                See https://boto3.amazonaws.com/v1/documentation/api/1.9.46/guide/configuration.html#configuring-credentials for alternative methods of authentication.

            aws_region (str):
                The AWS region to use, e.g. `us-west-1`, `us-west-2`, etc.

            **kwargs (Any):
                Any valid AWS CLI configuration file option. Full list is available here: https://boto3.amazonaws.com/v1/documentation/api/1.9.46/guide/configuration.html#configuration-file
                Note: Some configuration file options do not apply to the 'secretsmanager' client context. Use with discretion.
        """
        ...

    def get(self, key: str, default: Any = None):
        """
        Return a value from the configuration data key.

        Args:
            key (str):
                The configuration data key storing the value you'd like to retrieve
            default (str):
                The value returned if key is not found in configuration data
        """
        ...

    def get_by_prefix(self, prefix: str, trim_prefix: bool = False) -> dict[str, Any]:
        """
        Returns a dictionary containing configuration data items whose key starts with prefix.

        Args:
            prefix (str):
                A string containing the substring of characters that prefix a set of configuration data keys.

            trim_prefix (bool):
                If False, remove the prefix from dictionary keys.
                If True, don't remove the prefix from dictionary keys.
        """
        ...

    def set(self, key: str, value: Any):
        """
        Return a value from the configuration data key.

        Args:
            key (str):
                The configuration data key storing the value you'd like to set the value of
            value (str):
                The data you'd like to store under the key
        """
        ...

    def update(self, data: dict[str, Any] = None, **kwargs):
        """
        Updates the object's attributes with the data from the source.
        Attributes do not need to be declared in the class definition.

        args:
            data (dict):
                The key:value pairs to be loaded as class attributes
            **kwargs:
                Arbitrary keyword arguments, to be loaded as class attributes.
        """
        ...

    def delete_item(self, key: str):
        """
        Remove a key/value pair from the configuration data.

        Args:
            key (str):
                The configuration data key storing the value you'd like to delete
        """
        ...

    def clear_data(self, *keys: str):
        """
        Clears configuration data from the instance. If key is not found, nothing happens.
        args:
            *args (list[hashable]):
                A list of keys to clear from the instance. If None, all keys will be cleared.
        """
        ...

    def keys(self) -> list[str]:
        """
        Return a list of all configuration data keys
        """
        ...

    def values(self) -> list[Any]:
        """
        Return a list of all configuration data values
        """
        ...

    def items(self) -> list[tuple[str, Any]]:
        """
        Return a list of all configuration data as (key, value) tuples
        """
        ...

    def as_dict(self, copy: bool = True) -> dict[str, Any]:
        """
        Return the configuration data as a dict

        Args:
            copy (bool):
                If true (default), return a copy of the configuration data dict
                If false, return the actual configuration data dict.
        """
        ...
