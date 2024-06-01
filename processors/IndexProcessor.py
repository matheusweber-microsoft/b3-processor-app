import os
from exceptions.ProcessorExceptions import FileFormatNotSuportedError
from models.Message import Message
from repositories.CosmosRepository import CosmosRepository
from services.IndexingService import IndexingService
from services.Logger import Logger
from services.StorageContainerService import StorageContainerService

class IndexProcessor:
    logger = Logger()

    def __init__(self, storageContainerService: StorageContainerService, cosmosRepository: CosmosRepository):
        self.indexingService = IndexingService()
        self.storageContainerService = storageContainerService
        self.cosmosRepository = cosmosRepository

    def process(self, message: Message):
        self.logger.info("IP-01 - Starting index processor.")

        try:
            self.logger.info("IP-02 - Downloading file: " + message.storageFilePath)
            file = self.storageContainerService.download_blob(message.storageFilePath)

            if message.originalFileFormat in ['pdf', 'docx']:
                print("CONTINUE")    
            else:
                raise FileFormatNotSuportedError(message.originalFileFormat)
            
            print(file)
        except Exception as e:
            raise e
        pass