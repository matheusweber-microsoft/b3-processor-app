from models.ProcessorType import ProcessorType

class Message:
    def __init__(self, action: ProcessorType, fileId: str, storageFilePath: str, fileName: str, originalFileFormat: str, theme: str, subtheme: str, language: str):
        self.action = action
        self.fileId = fileId
        self.storageFilePath = storageFilePath
        self.fileName = fileName
        self.originalFileFormat = originalFileFormat
        self.theme = theme
        self.subtheme = subtheme
        self.language = language
    def to_string(self):
        return f"Action: {self.action}, File ID: {self.fileId}, Storage File Path: {self.storageFilePath}, File Name: {self.fileName}, Original File Format: {self.originalFileFormat}, Theme: {self.theme}, Subtheme: {self.subtheme}, Language: {self.language}"