from exceptions.MessageExceptions import InvalidMessageError, MalFormattedMessageException
from models.Message import Message
from models.IndexStatus import IndexStatus

class MessageBuilder:
    def __init__(self, dict):
        self.dict = dict
        self.message = None
        self.validate()

    def validate(self):
        # Check if message is a dictionary
        if not isinstance(self.dict, dict):
            raise InvalidMessageError("Message must be a dictionary")

        # Check if message contains all necessary keys
        necessary_keys = ['action', 'fileId', 'storageFilePath', 'fileName', 'originalFileFormat', 'theme', 'subtheme', 'language']
        
        if not all(key in self.dict for key in necessary_keys):
            raise InvalidMessageError("Message is missing necessary keys")
        
        try:
            self.messageType = IndexStatus(self.dict['action'])
        except:
            raise MalFormattedMessageException("Invalid action type")

        self.message = Message(self.dict)
        self.message.action = self.messageType
        return self

    def build(self) -> Message:
        # If all checks pass, return the message
        return self.message