import os
from models.MessageType import MessageType

class Message:
    def __init__(self, data: dict):
        self.action = data.get('action')
        self.fileId = data.get('fileId')
        self.storageFilePath = data.get('storageFilePath')
        self.fileName = data.get('fileName')
        self.originalFileFormat = data.get('originalFileFormat')
        self.theme = data.get('theme')
        self.subtheme = data.get('subtheme')
        self.language = data.get('language')
        
    def to_string(self):
        return f"Action: {self.action}, File ID: {self.fileId}, Storage File Path: {self.storageFilePath}, File Name: {self.fileName}, Original File Format: {self.originalFileFormat}, Theme: {self.theme}, Subtheme: {self.subtheme}, Language: {self.language}"
    
    def file_path_without_extension(self):
        file_path_without_extension, _ = os.path.splitext(self.storageFilePath)
        return file_path_without_extension + "1"