import os
from infra.KeyVault import KeyVault
from models.Message import Message
from processors.Processor import Processor
from repositories.CosmosRepository import CosmosRepository
from services.AzureSearchEmbedService import AzureSearchEmbedService
from services.StorageContainerService import StorageContainerService

class ProcessorBuilder:
    def __init__(self):
        key_vault = KeyVault()
        cosmos_db_connection_string_secret = key_vault.get_secret(os.getenv('KEY_VAULT_COSMOS_DB_NAME'))
        cosmos_db_database_name = os.getenv('DATABASE_NAME')
        self.storage_container_service = StorageContainerService()
        self.cosmos_repository = CosmosRepository(connection_string=cosmos_db_connection_string_secret, 
                                                 database_name=cosmos_db_database_name)
        self.search_embed_service = AzureSearchEmbedService(storage_container_service=self.storage_container_service)

    def build(self, message: Message) -> Processor:
        return Processor(
            message=message,
            storage_container_service=self.storage_container_service,
            cosmos_repository=self.cosmos_repository,
            search_embed_service=self.search_embed_service
        )
