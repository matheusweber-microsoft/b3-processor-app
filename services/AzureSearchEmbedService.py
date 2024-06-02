import os
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.identity import DefaultAzureCredential

class AzureSearchEmbedService:
    def __init__(self):
        azure_search_service_endpoint = os.getenv('AZURE_SEARCH_SERVICE_ENDPOINT')
        self.search_index_client = SearchIndexClient(
            endpoint=azure_search_service_endpoint,
            credential=DefaultAzureCredential(),
        )

    def get_index(self, index):
        index = self.search_index_client.get_index(index)
        return index