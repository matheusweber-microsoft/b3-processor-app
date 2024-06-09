import asyncio
import os
from models.Message import Message
from repositories.CosmosRepository import CosmosRepository
from services.Logger import Logger
from services.StorageContainerService import StorageContainerService
from azure.search.documents import SearchClient
from azure.identity import DefaultAzureCredential

class DeleteProcessor:
    
    def __init__(self, cosmos_repository: CosmosRepository, storage_container_service: StorageContainerService):
        self.logger = Logger()
        self.cosmos_repository = cosmos_repository
        self.storage_container_service = storage_container_service

    async def process(self, message: Message):
        self.logger.info("DP-PR-01 - Starting delete processor.")

        document = self.cosmos_repository.get_by_id("documentskb", message.fileId)

        if document is None:
            self.logger.error("DP-PR-02 - Document not found or document is not ready to be deleted Check Index Status. FileId: "+message.fileId)
            return
        
        self.storage_container_service.delete_blob("originaldocuments", message.storageFilePath)
        self.storage_container_service.delete_blobs_in_folder("documentpages", message.file_path_without_extension())
        self.storage_container_service.delete_blobs_in_folder("corpus", message.file_path_without_extension())    
        await self.remove_from_index_async(message)
        self.cosmos_repository.delete("documentskb", message.fileId)

    async def remove_from_index_async(self, message: Message):
        search_index_name = self.get_azure_search_index_name_for(message)

        self.logger.info(f"DP-RI-01 - Removing sections from original document '{message.storageFilePath}' from search index '{search_index_name}' for file {message.fileId}")

        search_client = SearchClient(endpoint=os.getenv('AZURE_SEARCH_SERVICE_ENDPOINT'),
                                     index_name=self.get_azure_search_index_name_for(message),
                                     credential=DefaultAzureCredential()
                                    )
        while True:
            filter = f"originaldocsource eq '{message.storageFilePath}'"
            
            result = search_client.search(
                search_text="", filter=filter, top=1000, include_total_count=True
            )

            result_count = result.get_count()
            
            if result_count == 0:
                self.logger.info("DP-RI-02 - No more sections to remove from search index "+search_index_name+" from original document "+message.storageFilePath+".")
                break

            documents_to_remove = []

            for document in result:
                documents_to_remove.append({"id": document["id"]})

            self.logger.info(str(len(documents_to_remove)) + " documents to remove")
            if len(documents_to_remove) == 0:
                self.logger.info("DP-RI-03 - No more sections to remove from search index "+search_index_name+" from original document "+message.storageFilePath+".")
                break

            removed_docs = search_client.delete_documents(documents_to_remove)
            self.logger.info("DP-RI-03 - Removed "+str(len(removed_docs))+" sections from search index "+search_index_name+" from original document "+message.storageFilePath+".")

            # It can take a few seconds for search results to reflect changes, so wait a bit
            await asyncio.sleep(2)

        if removed_docs != None:
            self.logger.info("DP-RI-04 - Removed "+str(len(removed_docs))+" sections from search index "+search_index_name+" from original document "+message.storageFilePath+".")


    def get_azure_search_index_name_for(self, message: Message):
        return message.theme + "-index-" + message.language