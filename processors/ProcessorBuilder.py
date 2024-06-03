from models.Message import Message
from processors.Processor import Processor
from services.StorageContainerService import StorageContainerService


class ProcessorBuilder:
    def __init__(self):
        self.storageContainerService = StorageContainerService()

    def build(self, message: Message) -> Processor:
        return Processor(
            message=message,
            storageContainerService=self.storageContainerService
        )