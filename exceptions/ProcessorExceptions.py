class ActionNotSupportedError(Exception):
    def __init__(self):
        super().__init__(f"""Action not supported""")

class FileFormatNotSuportedError(Exception):
    def __init__(self, format):
        super().__init__(f"File format not supported, format: " + format)