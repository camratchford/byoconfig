import logging
import json
from json import JSONDecodeError

import boto3
from boto3.exceptions import Boto3Error

from byoconfig.error import BYOConfigError
from byoconfig.sources.base import BaseVariableSource

logger = logging.getLogger(__name__)


class SecretsManagerVariableSource(BaseVariableSource):
    """
    A VariableSource that loads data from JSON encoded AWS Secrets Manager variables.
    """

    _metadata: set[str] = BaseVariableSource._metadata.union(
        {"_secrets_manager_client"}
    )

    def _create_secrets_manager_client(self, **aws_client_kwargs):
        try:
            self._secrets_manager_client = boto3.client(
                service_name="secretsmanager", **aws_client_kwargs
            )

        except Boto3Error as e:
            raise BYOConfigError(
                f"Encountered an unhandled boto3 error while creating the Secrets Manager client: {e.args}",
                self,
            ) from e
        except Exception as e:
            raise BYOConfigError(
                f"Encountered an unhandled exception while creating the Secrets Manager client: {e.args}",
                self,
            ) from e

    def load_from_secrets_manager(self, **aws_client_kwargs):
        secret_name = aws_client_kwargs.pop("aws_secret_name", None)
        if secret_name is None:
            return

        self._create_secrets_manager_client(**aws_client_kwargs)

        get_secret_value_response = self._secrets_manager_client.get_secret_value(
            SecretId=secret_name
        )
        if "SecretString" in get_secret_value_response:
            secret_payload = get_secret_value_response["SecretString"]
        else:
            secret_payload = get_secret_value_response["SecretBinary"]
        try:
            configuration_data = json.loads(secret_payload)
            logger.debug(
                f"Loaded configuration data from AWS SecretsManager secret '{secret_name}'"
            )

            self.update(configuration_data)

        except JSONDecodeError as e:
            raise BYOConfigError(
                f"Encountered a JSON decode error while parsing secret payload: {e.args}",
                self,
            ) from e

    # def dump_to_secrets_manager(self, **aws_client_kwargs):
    #     ...
    #     # todo:
