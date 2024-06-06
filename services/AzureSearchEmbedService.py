import os
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.identity import DefaultAzureCredential
from services.Logger import Logger

from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
    VectorSearchVectorizer,
)

class AzureSearchEmbedService:
    def __init__(self):
        self.logger = Logger()
        azure_search_service_endpoint = os.getenv('AZURE_SEARCH_SERVICE_ENDPOINT')
        self.search_index_client = SearchIndexClient(
            endpoint=azure_search_service_endpoint,
            credential=DefaultAzureCredential(),
        )
        
    async def ensure_search_index_exists(self, search_index_name):
        self.logger.info("ASES-COUI-01 - Creating or update the index called.")

        vector_search_config_name = "b3-vector-config"
        vector_search_profile = "b3-vector-profile"
        content_lang = search_index_name.split("-")[-1]

        analyzer_name = 'pt-BR.microsoft' if content_lang == 'port' else 'en.microsoft'

        self.logger.info("ASES-COUI-02 - Creating fields.")
        fields = [
            SimpleField(name="id", type="Edm.String", key=True),
            SearchableField(
                name="content",
                analyzer_name=analyzer_name
            ),
            SimpleField(
                name="sourcepage",
                type="Edm.String",
                filterable=True,
                facetable=True,
            ),
            SimpleField(
                name="sourcefile",
                type="Edm.String",
                filterable=True,
                facetable=True,
            ),
            SimpleField(
                name="theme",
                type="Edm.String",
                filterable=True,
                facetable=True,
            ),
            SimpleField(
                name="subtheme",
                type="Edm.String",
                filterable=True,
                facetable=True,
            ),
            SimpleField(
                name="originaldocsource",
                type="Edm.String",
                filterable=True
            ),
            SearchField(name="contentvector", 
                        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        searchable=True,
                        vector_search_dimensions=1536,
                        vector_search_profile_name=vector_search_profile
            )
        ]

        self.logger.info("ASES-COUI-03 - Creating index.")
        index = SearchIndex(
            name=search_index_name,
            fields=fields,
            semantic_search=SemanticSearch(
                configurations=[
                    SemanticConfiguration(
                        name="default",
                        prioritized_fields=SemanticPrioritizedFields(
                            title_field=None, content_fields=[SemanticField(field_name="content")]
                        ),
                    )
                ]
            ),
            vector_search=VectorSearch(
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name=vector_search_config_name
                    )
                ],
                profiles=[
                    VectorSearchProfile(
                        name=vector_search_profile,
                        algorithm_configuration_name=vector_search_config_name
                    ),
                ]
            ),
        )

        self.logger.info("ASES-COUI-04 - Checking if exists or not.")
        if search_index_name not in [name async for name in self.search_index_client.list_index_names()]:
            self.logger.info("ASES-COUI-05 - Creating " + search_index_name + " search index.")
            await self.search_index_client.create_index(index)
        else:
            self.logger.info("ASES-COUI-05 - Search index " + search_index_name + " already exists.")