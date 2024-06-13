import datetime
from io import BytesIO
from pathlib import Path
import tempfile
from models.DocumentsKBPage import DocumentsKBPage
from models.IndexStatus import IndexStatus
from models.Message import Message
from azure.search.documents import SearchClient
from repositories.CosmosRepository import CosmosRepository
from services.AzureSearchEmbedService import AzureSearchEmbedService
from services.Logger import Logger
from services.StorageContainerService import StorageContainerService


class DocDocumentProcessor:
    def __init__(self, storage_container_service: StorageContainerService, search_embed_service: AzureSearchEmbedService, cosmos_repository: CosmosRepository):
        self.storage_container_service = storage_container_service
        self.search_embed_service = search_embed_service
        self.cosmos_repository = cosmos_repository
        self.logger = Logger()

    async def process(self, message: Message, document_processed_memory_stream: BytesIO, search_client: SearchClient):
        self.logger.info("DP-PR-01 - Starting document processor.")

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as temp_file:
            temp_file.write(document_processed_memory_stream.getvalue())

            # Close the temporary file so it can be reopened in binary mode
            temp_file.close()

            # Reopen the temporary file in binary mode and read its contents
            with open(temp_file.name, "rb") as binary_file:
                doc_bytes = binary_file.read()

        self.storage_container_service.upload_page_blob(message.storageFilePath, doc_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        self.logger.info("DP-PR-02 - Successfully updated document.")

        metadata = DocumentsKBPage(
            file_page_name=message.fileName,
            storage_file_path=message.storageFilePath,
            page_number=1,
            index_status=IndexStatus.INDEXED.value,
            index_completion_date=int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
        )

        self.logger.info("DP-PR-03 - Created metadata for document page. Metadata: "+metadata.to_string())

        document_page_name = f"{Path(message.fileName).stem}.docx"
        document_page_full_path = f"{message.file_path_without_extension()}/{document_page_name}"

        embed_result = await self.search_embed_service.embed_blob(
            file_stream=BytesIO(doc_bytes),
            message=message,
            search_client=search_client,
            page_full_path=document_page_full_path
        )

        if embed_result == True:
            self.logger.info("DP-PR-04 - Successfully embedded document.")

            self.logger.info("DP-PR-05 - Updating Cosmos with the list of pages.")

            result = self.cosmos_repository.update_document_page_async("documentskb", message.fileId, metadata.to_dict())

            self.logger.info("DP-PR-06 - Status: " + str(result) + " for updating Cosmos with the metadata.")
        else:
            self.logger.error("DP-PR-04 - Error embedding document.")
        