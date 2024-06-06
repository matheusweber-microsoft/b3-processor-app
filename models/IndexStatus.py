from enum import Enum

class IndexStatus(Enum):
    DELETE = "delete"
    INDEX = "index"
    PROCESSING = "Processing"
    INDEXED = "Indexed"

    @staticmethod
    def get_processor_type(type_string):
        try:
            return IndexStatus[type_string.upper()]
        except KeyError:
            raise ValueError(f"Invalid processor type: {type_string}")