# Introduction 
The Ingestion Service is a background service which gets triggered based on an async message received to azure storage queue, this service is running continuously in the background and hosted on Azure Functions.

The service is responsible to do 2 things based on the incoming async message type:
1. Index and embed document chunks (vector representation) into the system knowledge base database (Azure AI Search), and store document metadata information in the Document Metadata Store (Mongo DB)
2. Delete already indexed documents from the the system knowledge database (Azure AI Search Index), remove proceed documents pages from Azure Storage, and from Document Metadata Store (Mongo DB).

## Message Types
The async messages will be published from the Ingestion Application to the Azure Storage Queue named `original-docs-action-received` and it can handle 2 types of messages. First is indexing of a new document, and the second is deleting and existing document.
### 1. Index a new document 
The async message content received when a new document needs to be indexed is the following, the `action` property will always be `index`:

```
{
  "action": "index",
  "fileId": "73606be1-397e-4e3c-90c6-79a166ca821f",
  "storageFilePath": "manualsoperations/counter/B3 Clearinghouse Rules.pdf",
  "fileName": "B3 Clearinghouse Rules.pdf",
  "originalFileFormat": "pdf",
  "theme": "manualsoperations",
  "subtheme": "counter",
  "language": "eng"
}
```
##### Message Properties
The properties of the message are the following:
- `action` property: Identifies the type of processing needed, allowed values are `index` or `delete`.
- `fileId` property: Identifies the unique identifier of the document stored in Document metadata store (Mongo DB).
- `storageFilePath` property: Identifies the storage location of the original file stored in Azure Storage container named `originaldocuments`.
- `fileName` property: Identifies the original file name
- `originalFileFormat` property: Identifies the file format of the document, allowed values are `pdf` or `docx`.
- `theme` property: Identifies which theme the file belongs to.
- `subtheme` property: Identifies which subtheme the file belongs to.
- `language` property: Specify the type of the Lexical Analyzer. Allowed values are `port` or `eng`. For the deployed application, the value will be always `port`. This could be useful if B3 is planning in the future to index documents in English language for theme and subtheme which only has English documents.

#### Process for indexing a new document
When a new async messages published the queue with an action of `index`, the processor picks up the message and start the following:

The service checks if the search index already exists based on the `theme`, `subtheme`, and `language` properties in the async message, if the index is not found, the service will create the search index. If it was found, then it will use this search index to store the new document. The index name uses this pattern `<theme>-index-<lang>`.

Then, it opens the original PDF document and start iterating through each page of the PDF document.
For each page, it performs the following steps:
- Saves the current page of the PDF document into Azure Storage Container named `documentpages`. The PDF page will be stored in the container using this pattern `<theme>/<subtheme>/<document file name><document file name>-<page sequence>.<file extension>` i.e. `manualsoperations/counter/B3 Clearinghouse Rules/B3 Clearinghouse Rules-1.pdf`

- Starts the embedding and indexing process for this page (see section [Embedding and indexing process](#embedding-and-indexing-process) for full details)


##### Embedding and indexing process

1. The Embedding and indexing process starts with extracting the text from the pdf page using the Azure Document Intelligence Service using the model `prebuilt-layout`.

1. Then it starts creating a sections (chunks) for the page, the splitting of the text into sections is based on a maximum section length (1000 Chars), sentence search limit, and section overlap (100 Chars). This will approximately create sections/chunks of 250 Tokens with overlap of 10% between each section.  

1. Those sections get stored for logging purpose into a container named `corpus` using the pattern `<theme>/<subtheme>/<document file name><document file name>-<page sequence>-<section sequence>.txt`

1. Before indexing the section into Azure AI Search Index, the service needs to generate embeddings (vector representation) of the section's content. The embeddings are obtained using the specified deployment name `text-embedding-ada-002` and the content of the section with carriage returns replaced by spaces. 

1. When the embeddings are generated, the service executes a batch indexing operation for the sections, it is configured to index 1000 sections or less in a batch.

1. Lastly, the service will update the Document metadata store to indicate that a certain page has been embedded and indexed successfully.

When the processing of all pages in the documents is completed, the service updates the status of the indexed original PDF document and sets the completion date of the indexing process in the Document metadata store.

> :information_source: When the original document is of type `docx`, the process remains the same, the only difference that the service will not break the docx into pages, it will treat the entire document as one single page, as well it will use the Document Intelligence model named `prebuilt-read` to extract the text from the docx document. Creating sections, embedding and indexing remains the same. 


### 2. Delete an existing document
The async message content received when an existing document needs to be removed from Azure AI Search Index, Document metadata store, and Azure storage is the following, the `action` property will always be `delete`: 

```
{
  "action": "delete",
  "fileId": "9685295a-f1d3-473b-b198-91681a47e680",
  "storageFilePath": "manualsoperations/counter/B3 Trading Rules.pdf",
  "fileName": "B3 Trading Rules.pdf",
  "originalFileFormat": "pdf",
  "theme": "manualsoperations",
  "subtheme": "counter",
  "language": "eng"
}
```

#### Process for deleting an existing document
When a new async messages published the queue with an action of `delete`, the processor picks up the message and start the following:

The service checks in the Document metadata store if the document is ready to be deleted by checking the existence of the document using the `fileId` property as well checking if the index status of the document is equal to 'Deleting', if both conditions are met the delete process starts in the following order:

1. Delete the original uploaded document from Azure Storage container `originaldocumets`.
1. Delete all document pages for the subject document from Azure Storage container `documentpages`.
1. Delete all document pages sections corpus for the subject document from Azure Storage container `corpus`.
1. Remove all the indexed sections from Azure AI Search Index for the subject document by using the property `storageFilePath` to filter all the indexed sections into Azure AI Search Index and compare it against the field `originaldocsource` in Azure AI Search Index.
1. Lastly, it deletes the record from Document Metadata store (Mongo DB) using the `fileId` property.

## Deploying Ingestion Service to Azure Functions

The ingestion service is deployed to Azure Function as a docker image, this means that we need to push a docker image to the Azure Container Registry and then deploy this image to Azure Function.

The Azure function is configured to enable Continuous Deployment via a Webhook URL, this means that when an image tagged with `latest` is pushed to Azure Container Registry, the Azure Function will be notified that there is a new image in ACR, and the Azure Function will pull the image from ACR and deploy this image. Note that permission `AcrPull` should be granted to the Azure Function in order to pull images from ACR.

To build the image and push it to ACR from a developer machine which has access to the code, we can do the following using PowerShell:

```PS
cd <local path>\b3gpt\ti-ea-processor-py-b3gpt 
$RESOURCE_GROUP="azr-rg-tech-ia-b3gpt-dev-n"
$ACR_NAME="azracrtechian"
$FUNCAPP_PY_NAME = "azr-fct-tech-ia-b3gpt-dev-n"

az acr build --registry $ACR_NAME --image "$($FUNCAPP_PY_NAME):latest" --file 'Dockerfile' .
```

The `az acr build` will use `docker build` and `docker push` to build the image and push it to ACR, once the image pushed to ACR, the  webhook named `b3gptingestionwebhook` will push a notification to Azure Function to start pulling the latest image.


## Azure Function Identity and Environment variables

#### Azure Function Identity
The processor is configured to use Managed Identity to allow it easily access other Microsoft Entra ID protected resources such as Azure Key Vault. Azure Storage Account, Azure AI Search, etc.. With Managed Identity enabled, connecting to other resources protected by Microsoft Entra ID can happen without connection strings or secrets. The type of identity configured for the processor is a **system-assigned identity** which is tied to the processor application, so if the app is deleted, the identity will be deleted.

In order for the processor to connect to the other services, the below Role Based Access Control permissions are needed:

- Azure Container Registry 
  - "AcrPull" Role (7f951dda-4ed3-4680-a7ca-43fe172d538d), to be able to pull artifacts from ACR.
- Azure Storage Queues
  - "Storage Queue Data Message Processor" Role (8a0f0c08-91a1-4084-bc3d-661d67233fed), to be able to pull messages from Azure Storage Queue.
   - "Storage Queue Data Contributor" Role (974c5e8b-45b9-4653-ba55-5f855dd0fb88), to be able to write messages to Azure Storage Queue incase of writing poison messages.
- Azure Blob Storage
  - "Storage Blob Data Contributor" Role (ba92f5b4-2d11-453d-a403-e96b0029c9fe), to be able to read/write/delete blobs to Azure Storage Containers.
- Azure Document Intelligence
  - "Cognitive Services User" Role (a97b65f3-24c7-4388-baec-2e87135dc908), to be able to access Document Intelligence and read text from PDF/Docx files.
- Azure Open AI
  - "Cognitive Services OpenAI User" Role (5e0bd9bd-7b93-4f28-af87-19fc36ad61bd), to be able to access Azure Open AI embedding model and generate vectors/embeddings.
- Azure AI Search
  - "Search Service Contributor" Role (7ca78c08-252a-4471-8644-bb5ff32d4ba0), to be able to manage Search Service and create Search Indexes
  - "Search Index Data Contributor" Role (8ebe5a00-799e-43f5-93ac-243d3dce84a7), to be able to access Azure Search Index and store data in indexes.
  - "Search Index Data Reader" Role (1407120a-92aa-4202-b7e9-c0e197c71c8f), to be able to access Azure Search Index and read data from the indexes.
- Azure Key Vault
  - "Key Vault Secrets User" Role (4633458b-17de-408a-b874-0445c86b69e6), to be able to access Azure Key Vault Secrets and read them.

There are 2 connection strings stored in Azure Key Vault which they are Cosmos DB (Mongo DB) connection string and Application Insights Connection string.

## Environment Variables

The Azure Function relies on the following environment variables for its configuration:

- `AzureWebJobsStorage`: The data plane URI of the queue service to which the processor connecting, using the HTTPS scheme. i.e. `https://<storage_account_name>.queue.core.windows.net/`
- `KEY_VAULT_NAME_ENDPOINT`: The data plane URI of the Azure Key Vault to which the processor connecting, using the HTTPS scheme. i.e. `https://<key_vault_name>.vault.azure.net/`
- `AZURE_SEARCH_SERVICE_ENDPOINT`: The data plane URI of the Azure AI Search Service to which the processor connecting, using the HTTPS scheme. i.e. `https://<search_service_name>.search.windows.net/` 
- `KEY_VAULT_COSMOS_DB_CONN_NAME`: The name of the secret in AKV which stores the Mongo DB connection string in it.
- `DATABASE_NAME`: The MongoDB Database name.
- `AZURE_OPENAI_SERVICE_ENDPOINT`: The data plane URI of the Azure Open AI Service to which the processor connecting, using the HTTPS scheme. i.e. `https://<openai_service_name>.openai.azure.com/` 
- `EMBEDDING_DEPLOYMENT_NAME`: The name of embedding model deployed in the Open AI Service.
- `AZURE_FORM_RECOGNIZER_SERVICE_ENDPOINT`: The data plane URI of the Azure Document Intelligence Service to which the processor connecting, using the HTTPS scheme. i.e. `https://<doc_intelligence_service_name>.cognitiveservices.azure.com/` 
- `APPLICATIONINSIGHTS_CONNECTION_STRING`: The Application Insights connection string.
- `AZURE_STORAGE_BLOB_ENDPOINT`: The data plane URI of the bloc service to which the processor connecting, using the HTTPS scheme. i.e. `https://<storage_account_name>.blob.core.windows.net/`

Make sure to set these environment variables correctly before deploying and running the Azure Function.
