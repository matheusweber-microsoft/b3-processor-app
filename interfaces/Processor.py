from abc import ABC, abstractmethod
from models.Message import Message

class Processor(ABC):
    message: Message
    
    def __init__(self, message):
        self.message = message

    @abstractmethod
    def process(self):
        pass

class DeleteProcessor(Processor):

    def process(self):
        pass

class IndexProcessor(Processor):

    def process(self):
        pass