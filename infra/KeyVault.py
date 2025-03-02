from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import os

class KeyVault:
    def __init__(self):
        self.credential = DefaultAzureCredential()
        self.key_vault_uri = os.getenv('KEY_VAULT_NAME_ENDPOINT')
        if self.key_vault_uri is None:
            raise ValueError("KEY_VAULT_NAME_ENDPOINT environment variable is not set")
        self.client = SecretClient(vault_url=self.key_vault_uri, credential=self.credential)

    def get_secret(self, secret_name):
        return self.client.get_secret(secret_name).value