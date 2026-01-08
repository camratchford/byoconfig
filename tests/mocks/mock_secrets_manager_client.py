class MockSecretsManagerClient:
    """Mock AWS Secrets Manager client with the same interface as boto3."""

    def __init__(self):
        self.secrets = {}

    def add_secret(
        self, secret_id: str, secret_string: str = None, secret_binary: bytes = None
    ):
        """Helper to add secrets for testing."""
        self.secrets[secret_id] = {
            "SecretString": secret_string,
            "SecretBinary": secret_binary,
        }

    def get_secret_value(self, SecretId: str):
        """Mock implementation of get_secret_value."""
        if SecretId not in self.secrets:
            from botocore.exceptions import ClientError

            raise ClientError(
                {
                    "Error": {
                        "Code": "ResourceNotFoundException",
                        "Message": f"Secrets Manager can't find the specified secret: {SecretId}",
                    }
                },
                "GetSecretValue",
            )

        secret = self.secrets[SecretId]
        response = {
            "ARN": f"arn:aws:secretsmanager:us-east-1:123456789012:secret:{SecretId}"
        }

        if secret["SecretString"] is not None:
            response["SecretString"] = secret["SecretString"]
        elif secret["SecretBinary"] is not None:
            response["SecretBinary"] = secret["SecretBinary"]

        return response
