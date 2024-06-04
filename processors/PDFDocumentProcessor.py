from io import BytesIO
from models.Message import Message
from services.Logger import Logger
from azure.search.documents import SearchClient
from PyPDF2 import PdfWriter, PdfReader
import os
from pathlib import Path
from services.StorageContainerService import StorageContainerService
import tempfile

class PDFDocumentProcessor:
    def __init__(self, storage_container_service: StorageContainerService):
        self.logger = Logger()
        self.storage_container_service = storage_container_service

    def process(self, message: Message, document_processed_memory_stream: BytesIO, search_client: SearchClient):
        self.logger.info("DP-PR-01 - Starting document processor.")

        self.logger.info("DP-PR-02 - Opening PDF.")
        pdf_reader = PdfReader(document_processed_memory_stream)
        self.logger.info("DP-PR-03 - Successfully opened original pdf document: +" + message.fileName + ". Pages count: " + str(len(pdf_reader.pages)))

        for i in range(len(pdf_reader.pages)):
            document_page_name = f"{Path(message.fileName).stem}-{i + 1}.pdf"
            document_page_full_path = f"{message.file_path_without_extension()}/{document_page_name}"
            
            self.logger.info("DP-PR-04 - Start working on pdf page: " + document_page_full_path)

            single_pdf_document = PdfWriter()
            single_pdf_document.add_page(pdf_reader.pages[i])

            self.logger.info("DP-PR-05 - Created a new document with the page.")

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf_file:
                single_pdf_document.write(temp_pdf_file)

                # Close the temporary file so it can be reopened in binary mode
                temp_pdf_file.close()

                # Reopen the temporary file in binary mode and read its contents
                with open(temp_pdf_file.name, "rb") as binary_file:
                    pdf_bytes = binary_file.read()

            self.logger.info("DP-PR-05 - Uploading document for blob.")
            
            self.storage_container_service.upload_page_blob(document_page_full_path, pdf_bytes)

            self.logger.info("DP-PR-06 - Successfully updated document.")

