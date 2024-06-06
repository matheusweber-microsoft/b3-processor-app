import datetime
from io import BytesIO
import os
from exceptions.ProcessorExceptions import FileFormatNotSuportedError
from models.Message import Message
from models.IndexStatus import IndexStatus
from processors.PDFDocumentProcessor import PDFDocumentProcessor
from repositories.CosmosRepository import CosmosRepository
from services.AzureSearchEmbedService import AzureSearchEmbedService
from services.Logger import Logger
from services.StorageContainerService import StorageContainerService
from azure.search.documents import SearchClient
from azure.identity import DefaultAzureCredential

class IndexProcessor:
    logger = Logger()

    def __init__(self, storage_container_service: StorageContainerService, cosmos_repository: CosmosRepository, search_embed_service: AzureSearchEmbedService):
        self.storage_container_service = storage_container_service
        self.cosmos_repository = cosmos_repository
        self.search_embed_service = search_embed_service

    async def process(self, message: Message):
        self.logger.info("IP-01 - Starting index processor.")

        original_file_name = message.fileName
        original_file_path = message.storageFilePath
        file_id = message.fileId

        self.logger.info("IP-02 - Checking if file format is supported.")
        
        if message.originalFileFormat in ['pdf', 'docx']:
            self.logger.info("IP-03 - Updating document index for: " + original_file_name + " with ID: " + file_id)
            self.cosmos_repository.update("documentskb", file_id, {"index_status": IndexStatus.PROCESSING.value})

            try:
                self.logger.info("IP-04 - Downloading blob file: " + message.storageFilePath)

                file_memory_stream = BytesIO(self.storage_container_service.download_blob(message.storageFilePath).readall())
                self.logger.info("IP-05 - Success downloading blob file and store in a memory stream")

                search_index_name = self.get_azure_search_index_name_for(message)
                self.logger.info("IP-06 - Get index name: " + search_index_name)

                self.logger.info("IP-07 - Ensure the index exists")
                await self.search_embed_service.ensure_search_index_exists(search_index_name)

                if message.originalFileFormat == 'pdf':
                    self.logger.info("IP-08 - Processing PDF document.")
                    pdf_processor = PDFDocumentProcessor(storage_container_service=self.storage_container_service, 
                                                         search_embed_service=self.search_embed_service,
                                                         cosmos_repository=self.cosmos_repository)
                    await pdf_processor.process(message, 
                                          file_memory_stream, 
                                          SearchClient(endpoint=os.getenv('AZURE_SEARCH_SERVICE_ENDPOINT'),
                                                       index_name=search_index_name,
                                                       credential=DefaultAzureCredential()
                                                    )
                                        )
                
                self.cosmos_repository.update_document_index_completion("documentskb", file_id, int(datetime.datetime.now(datetime.UTC).timestamp() * 1000))
            except Exception as e:
                raise e
        else:
            raise FileFormatNotSuportedError(message.original_file_format)
        
    def get_azure_search_index_name_for(self, message: Message):
        return message.theme + "-index-" + message.language