import os
from infra.KeyVault import KeyVault
from models.Message import Message
from processors.Processor import Processor
from repositories.CosmosRepository import CosmosRepository
from services.StorageContainerService import StorageContainerService


class ProcessorBuilder:
    def __init__(self):
        keyVault = KeyVault()
        cosmosDBConnectionStringSecret = keyVault.get_secret(os.getenv('KEY_VAULT_COSMOS_DB_NAME'))
        cosmosDBDatabaseName = os.getenv('DATABASE_NAME')
        self.storageContainerService = StorageContainerService()
        self.cosmosRepository = CosmosRepository(connection_string=cosmosDBConnectionStringSecret, 
                                                 database_name=cosmosDBDatabaseName)

    def build(self, message: Message) -> Processor:
        return Processor(
            message=message,
            storageContainerService=self.storageContainerService,
            cosmosRepository=self.cosmosRepository
        )