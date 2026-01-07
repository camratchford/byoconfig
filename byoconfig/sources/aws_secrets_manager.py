
import logging
import json
from json import JSONDecodeError
from os import getenv
from typing import Optional

import boto3
from boto3.exceptions import Boto3Error
import logging

from byoconfig.error import BYOConfigError
from byoconfig.sources.base import BaseVariableSource

logger = logging.getLogger(__name__)


class SecretsManagerVariableSource(BaseVariableSource):
    """
    A VariableSource that loads data from JSON encoded AWS Secrets Manager variables.
    """

    _metadata: set[str] = BaseVariableSource._metadata.union({'_secrets_manager_client'})

    def __init__(self, **kwargs):
        """
        Initialize an EnvVariableSource instance.

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
                The AWS region to use, e.g. us-west-1, us-west-2, etc.

            **kwargs (Any):
                Any valid AWS CLI configuration file option. Full list is available here: https://boto3.amazonaws.com/v1/documentation/api/1.9.46/guide/configuration.html#configuration-file
                Note: Some configuration file options do not apply to the 'secretsmanager' client context. Use with discretion.
        """

        aws_client_kwargs = {}

        # AWS client option might exist in the Config instance (via importing a config file)
        from_config_data = self.get_by_prefix("aws", trim_prefix=False)
        if from_config_data:
            aws_client_kwargs.update(from_config_data)

        # Method parameters should take precedence over those in a config file
        aws_client_kwarg_keys = self._get_by_prefix(kwargs, "aws", False)
        aws_client_kwargs.update({name.lower(): kwargs.pop(name) for name, _ in aws_client_kwarg_keys.items()})

        try:
            self.load_secrets_manager_secret(**aws_client_kwargs)
        except BYOConfigError as e:
            raise e
        except Boto3Error as e:
            raise BYOConfigError(
                f"Encountered a boto3 error while loading AWS Secrets Manager secret: {e.args}", self
            ) from e
        except Exception as e:
            raise BYOConfigError(
                f"Encountered an unhandled exception while loading AWS Secrets Manager secret: {e.args}", self
            ) from e

    def _create_secrets_manager_client(self, **aws_client_kwargs):
        try:
            self._secrets_manager_client = boto3.client(
                service_name='secretsmanager',
                **aws_client_kwargs
            )

        except Boto3Error as e:
            raise BYOConfigError(
                f"Encountered an unhandled boto3 error while creating the Secrets Manager client: {e.args}", self
            ) from e
        except Exception as e:
            raise BYOConfigError(
                f"Encountered an unhandled exception while creating the Secrets Manager client: {e.args}", self
            ) from e

    def load_secrets_manager_secret(self, **aws_client_kwargs):

        secret_name = aws_client_kwargs.pop("aws_secret_name", None)
        if secret_name is None:
            return

        self._create_secrets_manager_client(**aws_client_kwargs)

        get_secret_value_response = self._secrets_manager_client.get_secret_value(SecretId=secret_name)
        if 'SecretString' in get_secret_value_response:
            secret_payload = get_secret_value_response['SecretString']
        else:
            secret_payload = get_secret_value_response['SecretBinary']
        try:
            configuration_data = json.loads(secret_payload)
            logger.debug(f"Loaded configuration data from AWS SecretsManager secret '{secret_name}'")

            self.update(configuration_data)

        except JSONDecodeError as e:
            raise BYOConfigError(
                f"Encountered a JSON decode error while parsing secret payload: {e.args}", self
            ) from e
