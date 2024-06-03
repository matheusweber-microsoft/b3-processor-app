import os
from exceptions.ProcessorExceptions import FileFormatNotSuportedError
from models.Message import Message
from models.MessageType import MessageType
from repositories.CosmosRepository import CosmosRepository
from services.AzureSearchEmbedService import AzureSearchEmbedService
from services.Logger import Logger
from services.StorageContainerService import StorageContainerService

class IndexProcessor:
    logger = Logger()

    def __init__(self, storageContainerService: StorageContainerService, cosmosRepository: CosmosRepository, searchEmbedService: AzureSearchEmbedService):
        self.storageContainerService = storageContainerService
        self.cosmosRepository = cosmosRepository
        self.searchEmbedService = searchEmbedService

    async def process(self, message: Message):
        self.logger.info("IP-01 - Starting index processor.")

        originalFileName = message.fileName
        originalFilePath = message.storageFilePath
        fileId = message.fileId

        self.logger.info("IP-02 - Checking if file format is supported.")
        
        if message.originalFileFormat in ['pdf', 'docx']:
            self.logger.info("IP-03 - Updating document index for: " + originalFileName + " with ID: " + fileId)
            self.cosmosRepository.update("documentskb", fileId, {"indexStatus": MessageType.INDEXING.value})

            try:
                self.logger.info("IP-04 - Downloading blob file: " + message.storageFilePath)
                fileMemoryStream = self.storageContainerService.download_blob(message.storageFilePath)
                self.logger.info("IP-05 - Success downloading blob file and store in a memory stream")

                searchIndexName = self.get_azure_search_index_name_for(message)
                self.logger.info("IP-06 - Get index name: " + searchIndexName)

                self.logger.info("IP-07 - Creating or updating the index")
                await self.searchEmbedService.create_or_update_the_index_if_exists(searchIndexName)

            except Exception as e:
                raise e
        else:
            raise FileFormatNotSuportedError(message.originalFileFormat)
        
    def get_azure_search_index_name_for(self, message: Message):
        return message.theme + "-index-" + message.language