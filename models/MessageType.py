from enum import Enum

class MessageType(Enum):
    DELETE = "delete"
    INDEX = "index"
    INDEXING = "indexing"
    INDEXED = "Indexed"

    @staticmethod
    def get_processor_type(type_string):
        try:
            return MessageType[type_string.upper()]
        except KeyError:
            raise ValueError(f"Invalid processor type: {type_string}")