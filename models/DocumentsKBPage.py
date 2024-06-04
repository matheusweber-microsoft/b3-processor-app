class DocumentsKBPage:
    def __init__(self, file_page_name, storage_file_path, page_number, index_status, index_completion_date):
        self.file_page_name = file_page_name
        self.storage_file_path = storage_file_path
        self.page_number = page_number
        self.index_status = index_status
        self.index_completion_date = index_completion_date

    def to_string(self):
        return f"File Page Name: {self.file_page_name}\nStorage File Path: {self.storage_file_path}\nPage Number: {self.page_number}\nIndex Status: {self.index_status}\nIndex Completion Date: {self.index_completion_date}"
    
    def to_dict(self):
        return {
            "filePageName": self.file_page_name,
            "storageFilePath": self.storage_file_path,
            "pageNumber": self.page_number,
            "indexStatus": self.index_status,
            "indexCompletionDate": self.index_completion_date
        }