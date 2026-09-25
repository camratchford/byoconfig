from json import JSONDecodeError

import pytest

from byoconfig.sources import aws_secrets_manager
from byoconfig.sources.aws_secrets_manager import SecretsManagerVariableSource


class ExampleSecretsSource(SecretsManagerVariableSource):
    username: str = "admin"
    password: str = ""


class FakeSecretsManagerClient:
    def __init__(self, response):
        self.response = response
        self.requested_secret_ids = []

    def get_secret_value(self, SecretId):
        self.requested_secret_ids.append(SecretId)
        return self.response


@pytest.fixture
def client_calls():
    return []


@pytest.fixture
def use_fake_client(monkeypatch, client_calls):
    def install(response):
        fake_client = FakeSecretsManagerClient(response)

        def create_client(**client_kwargs):
            client_calls.append(client_kwargs)
            return fake_client

        monkeypatch.setattr(aws_secrets_manager.boto3, "client", create_client)
        return fake_client

    return install


@pytest.fixture
def source():
    return ExampleSecretsSource()


def test_load_secret_string(source, use_fake_client):
    fake_client = use_fake_client(
        {"SecretString": '{"username": "user", "password": "hunter2"}'}
    )

    source.load_from_secrets_manager("app/secret")

    assert source.get("username") == "user"
    assert source.get("password") == "hunter2"
    assert fake_client.requested_secret_ids == ["app/secret"]


def test_load_secret_binary(source, use_fake_client):
    use_fake_client({"SecretBinary": b'{"password": "hunter2"}'})

    source.load_from_secrets_manager("app/secret")

    assert source.get("password") == "hunter2"


def test_client_kwargs_are_passed_to_boto3(source, use_fake_client, client_calls):
    use_fake_client({"SecretString": "{}"})

    source.load_from_secrets_manager("app/secret", region_name="us-west-2")

    assert client_calls == [
        {"service_name": "secretsmanager", "region_name": "us-west-2"}
    ]


def test_no_secret_name_does_nothing(source, use_fake_client, client_calls):
    use_fake_client({"SecretString": '{"username": "user"}'})

    source.load_from_secrets_manager(None)

    assert client_calls == []
    assert source.get("username") == "admin"


def test_invalid_json_raises_value_error(source, use_fake_client):
    use_fake_client({"SecretString": "{"})

    with pytest.raises(ValueError) as error_info:
        source.load_from_secrets_manager("app/secret")

    assert isinstance(error_info.value.__cause__, JSONDecodeError)


def test_unknown_key_raises_key_error(source, use_fake_client):
    use_fake_client({"SecretString": '{"missing": "value"}'})

    with pytest.raises(KeyError):
        source.load_from_secrets_manager("app/secret")
