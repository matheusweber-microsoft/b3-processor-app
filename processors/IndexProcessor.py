from models.Message import Message
from services.Logger import Logger
from services.StorageContainerService import StorageContainerService

class IndexProcessor:
    logger = Logger()

    def __init__(self, storageContainerService: StorageContainerService):
        self.storageContainerService = storageContainerService

    def process(self, message: Message):
        self.logger.info("IP-01 - Starting index processor.")

        try:
            self.logger.info("IP-02 - Downloading file: " + message.storageFilePath)
            file = self.storageContainerService.download_blob(message.storageFilePath)
            print(file)
        except Exception as e:
            raise e
        pass