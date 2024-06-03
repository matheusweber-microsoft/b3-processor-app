class InvalidMessageError(Exception):
    def __init__(self):
        super().__init__(f"""Raised when the input message is invalid.""")

class MalFormattedMessageException(Exception):
    def __init__(self, message):
        super().__init__(f"Malformatted message: {message}")