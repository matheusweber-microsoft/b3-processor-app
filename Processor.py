from interfaces.Processor import DeleteProcessor, IndexProcessor, Processor
from models.Message import Message
from models.ProcessorType import ProcessorType
    
class Processor:
    def __init__(self, message: Message):
        self.message = message

    def process(self):
        pass

    def verify_message(self):
        pass
    def build(message: Message):
        processor_map = {
            ProcessorType.DELETE: DeleteProcessor(message),
            ProcessorType.INDEX: IndexProcessor(message),
        }
        return processor_map.get(type, None)