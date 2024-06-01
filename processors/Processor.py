from models.Message import Message
from models.ProcessorType import ProcessorType
from processors.IndexProcessor import IndexProcessor
from services.Logger import Logger
from services.StorageContainerService import StorageContainerService
    
class Processor:
    logger = Logger()
    
    def __init__(self, message: Message, storageContainerService: StorageContainerService):
        self.message = message
        self.indexProcessor = IndexProcessor(storageContainerService=storageContainerService)

    def process(self):
        self.logger.info("PR-01 - Starting processing the message for message: " + self.message.to_string())
        
        if self.message.action == ProcessorType.INDEX:
            self.logger.info("PR-02 - Starting index processor")
            self.indexProcessor.process(self.message)
        elif self.message.action == ProcessorType.DELETE:
            self.logger.info("PR-02 - Starting delete processor")
        pass
