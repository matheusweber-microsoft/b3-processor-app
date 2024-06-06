from io import BytesIO
import os
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.identity import DefaultAzureCredential
from openai import AsyncAzureOpenAI
from handlers.TextSplitterHandler import TextSplitterHandler
from models.Message import Message
from models.Page import Page, SplitPage
from models.PageDetail import PageDetail
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

from services.StorageContainerService import StorageContainerService
from azure.search.documents import SearchClient
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import DocumentTable
import html
from typing import IO, AsyncGenerator, Generator, List, Union
from azure.ai.formrecognizer import FormRecognizerClient
from azure.search.documents import IndexDocumentsBatch
from azure.ai.textanalytics.aio import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from azure.identity.aio import get_bearer_token_provider

class AzureSearchEmbedService:
    def __init__(self, storage_container_service: StorageContainerService):
        self.logger = Logger()
        azure_search_service_endpoint = os.getenv('AZURE_SEARCH_SERVICE_ENDPOINT')
        self.search_index_client = SearchIndexClient(
            endpoint=azure_search_service_endpoint,
            credential=DefaultAzureCredential(),
        )
        self.storage_container_service = storage_container_service
        self.text_splitter_handler = TextSplitterHandler()
        azure_open_ai_endpoint = os.getenv('AZURE_OPENAI_SERVICE_ENDPOINT')
        azure_deployment = os.getenv('EMBEDDING_DEPLOYMENT_NAME')
        
        self.credential = DefaultAzureCredential()

        auth_args = {}
        auth_args["azure_ad_token_provider"] = get_bearer_token_provider(
            self.credential, "https://cognitiveservices.azure.com/.default"
        )

        self.open_ai_client = AsyncAzureOpenAI(
            azure_endpoint=azure_open_ai_endpoint, 
            azure_deployment=azure_deployment,
            api_version="2023-05-15",
            **auth_args
        )

    async def ensure_search_index_exists(self, search_index_name):
        self.logger.info("ASES-COUI-01 - Creating the index if necessary")

        self.logger.info("ASES-COUI-04 - Checking if exists or not.")
        if search_index_name not in [name async for name in self.search_index_client.list_index_names()]:
            self.logger.info("ASES-COUI-05 - Creating " + search_index_name + " search index.")
            await self.create_index(search_index_name)
        else:
            self.logger.info("ASES-COUI-05 - Search index " + search_index_name + " already exists.")
    
    async def create_index(self, search_index_name: str) -> SearchIndex:
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

        await self.search_index_client.create_index(index)
    
    async def embed_blob(self, file_stream: BytesIO, message: Message, search_client: SearchClient, page_full_path: str) -> bool:
        try:
            self.logger.info("ASES-EB-01 - Start embedding blob "+page_full_path)

            page_map = await self.parse(file_stream=file_stream,
                                        blob_name=page_full_path,
                                        file_format=message.originalFileFormat)
            
            self.logger.info("ASES-EB-02 - Embedding text in Azure Search index. Page map count: " + str(len(page_map)))

            file_name_without_extension = os.path.splitext(os.path.basename(page_full_path))[0]
            directory = os.path.dirname(page_full_path)

            for page in page_map:
                corpus_page_name = file_name_without_extension + "-" + str(page.Index) + ".txt"
                corpus_name_full_path = os.path.join(directory, corpus_page_name)
                self.logger.info("ASES-EB-03 - Uploading corpus blob for " + corpus_page_name + " with path: " + corpus_name_full_path)
                corpus_text_file_stream = BytesIO(page.Text.encode('utf-8'))
                self.storage_container_service.upload_corpus_blob(corpus_name_full_path, corpus_text_file_stream)
            
            self.logger.info("ASES-EB-04 - Splitting text into sections.")

            sections = self.text_splitter_handler.split_pages(
                page_full_path=page_full_path,
                message=message,
                pages=page_map
            )
            
            self.logger.info("ASES-EB-05 - Indexing sections in into search index, number of sections: "+ str(len(sections)) +".")

            await self.index_section(sections, search_client)
        except:
            self.logger.error("ASES-EB-06 - Error embedding blob "+page_full_path)

        return True
    
    async def parse(self, file_stream: BytesIO, blob_name: str, file_format: str) -> List[PageDetail]:
        model_id = "prebuilt-layout" if file_format.lower() == "pdf" else "prebuilt-read"
        self.logger.info("ASES-GDT-01 - Extracting text from " + blob_name + " using Azure Form Recognizer")
        page_map = []

        file_format_formatted = "application/pdf" if file_format.lower() == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        async with DocumentIntelligenceClient(
            endpoint=os.getenv('AZURE_FORM_RECOGNIZER_SERVICE_ENDPOINT'), credential=DefaultAzureCredential()
        ) as document_intelligence_client:
            poller = await document_intelligence_client.begin_analyze_document(
                model_id=model_id, analyze_request=file_stream, content_type=file_format_formatted
            )
            form_recognizer_results = await poller.result()
            offset = 0

            for page_num, page in enumerate(form_recognizer_results.pages):
                tables_on_page = [
                    table
                    for table in (form_recognizer_results.tables or [])
                    if table.bounding_regions and table.bounding_regions[0].page_number == page_num + 1
                ]

                # mark all positions of the table spans in the page
                page_offset = page.spans[0].offset
                page_length = page.spans[0].length
                table_chars = [-1] * page_length
                for table_id, table in enumerate(tables_on_page):
                    for span in table.spans:
                        # replace all table spans with "table_id" in table_chars array
                        for i in range(span.length):
                            idx = span.offset - page_offset + i
                            if idx >= 0 and idx < page_length:
                                table_chars[idx] = table_id

                # build page text by replacing characters in table spans with table html
                page_text = ""
                added_tables = set()
                for idx, table_id in enumerate(table_chars):
                    if table_id == -1:
                        page_text += form_recognizer_results.content[page_offset + idx]
                    elif table_id not in added_tables:
                        page_text += AzureSearchEmbedService.table_to_html(tables_on_page[table_id])
                        added_tables.add(table_id)

                page_map.append(PageDetail(page_num, offset, page_text))
                offset += len(page_text)
        return page_map
        
    @classmethod
    def table_to_html(cls, table: DocumentTable):
        table_html = "<table>"
        rows = [
            sorted([cell for cell in table.cells if cell.row_index == i], key=lambda cell: cell.column_index)
            for i in range(table.row_count)
        ]
        for row_cells in rows:
            table_html += "<tr>"
            for cell in row_cells:
                tag = "th" if (cell.kind == "columnHeader" or cell.kind == "rowHeader") else "td"
                cell_spans = ""
                if cell.column_span is not None and cell.column_span > 1:
                    cell_spans += f" colSpan={cell.column_span}"
                if cell.row_span is not None and cell.row_span > 1:
                    cell_spans += f" rowSpan={cell.row_span}"
                table_html += f"<{tag}{cell_spans}>{html.escape(cell.content)}</{tag}>"
            table_html += "</tr>"
        table_html += "</table>"
        return table_html
    
    async def index_section(self, sections, search_client: SearchClient):
        self.logger.info("ASES-IS-01 - Indexing sections in Azure Search index.")
        iteration = 0

        batch = IndexDocumentsBatch()
        
        self.logger.info("ASES-IS-02 - Creating batch index with "+str(len(sections)) + " sections.")
        for section in sections:
            result = await self.open_ai_client.embeddings.create(
                model=os.getenv("EMBEDDING_DEPLOYMENT_NAME"), input=section.content
            )
            embedding = result.data[0].embedding
            
            document = {
                "id": section.id,
                "content": section.content,
                "sourcepage": section.source_page,
                "sourcefile": section.source_file,
                "theme": section.theme,
                "subtheme": section.sub_theme,
                "originaldocsource": section.original_doc_source,
                "contentvector": embedding,
            }

            batch.add_upload_actions([document])
            iteration += 1

            if iteration % 1000 == 0:
                self.logger.info(f"ASES-IS-03 - Indexing batch {iteration}")
                result = search_client.index_documents(batch)

                succeeded = 0
                for indexing_result in result:
                    if indexing_result.succeeded == True:
                        succeeded += 1

                self.logger.info(f"ASES-IS-04 - Result = "+str(result))
                self.logger.info(f"ASES-IS-04 - Indexed {len(batch.actions)} sections, {succeeded} succeeded")
                batch = IndexDocumentsBatch()

        if len(batch.actions) > 0:
            self.logger.info(f"ASES-IS-05 - Indexing batch {iteration}")
            result = search_client.index_documents(batch)

            succeeded = 0
            for indexing_result in result:
                if indexing_result.succeeded == True:
                    succeeded += 1

            self.logger.info(f"ASES-IS-04 - Result = "+str(result))
            self.logger.info(f"ASES-IS-06 - Indexed {len(batch.actions)} sections, {succeeded} succeeded")
            
        self.logger.info("ASES-IS-04 - Indexing completed.")