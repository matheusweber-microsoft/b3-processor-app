from exceptions.ProcessorExceptions import ActionNotSupportedError
from models.Message import Message
from models.MessageType import MessageType
from processors.IndexProcessor import IndexProcessor
from repositories.CosmosRepository import CosmosRepository
from services.AzureSearchEmbedService import AzureSearchEmbedService
from services.Logger import Logger
from services.StorageContainerService import StorageContainerService
    
class Processor:
    logger = Logger()
    
    def __init__(self, message: Message, storage_container_service: StorageContainerService, cosmos_repository: CosmosRepository, search_embed_service: AzureSearchEmbedService):
        self.message = message
        self.index_processor = IndexProcessor(storage_container_service=storage_container_service, 
                                             cosmos_repository=cosmos_repository, 
                                             search_embed_service=search_embed_service)

    async def process(self):
        self.logger.info("PR-01 - Starting processing the message for message: " + self.message.to_string())
        
        if self.message.action == MessageType.INDEX:
            self.logger.info("PR-02 - Starting index processor")
            await self.index_processor.process(self.message)
        elif self.message.action == MessageType.DELETE:
            self.logger.info("PR-02 - Starting delete processor")
        else:
            self.logger.error("PR-02 - Action provided not supported")
            raise ActionNotSupportedError()
