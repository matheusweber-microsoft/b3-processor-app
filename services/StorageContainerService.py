import os
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.identity import DefaultAzureCredential
from io import BytesIO
from exceptions.StorageContainerServiceExceptions import BlobFileDoesntExistsError
from services.Logger import Logger
from pathlib import Path


class StorageContainerService:

    def __init__(self):
        self.download_container_name = "originaldocuments"
        self.upload_pages_container_name = "documentpages"
        self.corpus_container_name = "corpus"
        self.logging = Logger()        
        self.logging.info('SCS-INIT-01 - Running in the serve with Default Azure Credentials')
        self.blob_service_client = BlobServiceClient(account_url=os.getenv('AZURE_STORAGE_BLOB_ENDPOINT'), 
                                                     credential=DefaultAzureCredential())

    def download_blob(self, blob_name):
        self.logging.info('SCS-DB-01 - Download blob method called')
        try:
            self.logging.info('SCS-DB-02 - Getting blob')
            
            blob_client = self.blob_service_client.get_blob_client(container=self.download_container_name, 
                                                                   blob=blob_name)
            if not blob_client.exists():
                self.logging.error(f"SCS-DB-03 - Blob does not exists in container.")
                raise BlobFileDoesntExistsError()
            
            # Create a stream and download the blob to it
            stream = BytesIO()
            downloader = blob_client.download_blob()
            downloader.readinto(stream)

            self.logging.info('SCS-DB-04 - Blob downloaded with success.')
            return blob_client.download_blob()   
        except Exception as e:
            self.logging.error(f"SCS-DB-03 - Error on downloading blob: {e}")
            raise e

    def upload_page_blob(self, container_name, data, content_type):
        self.logging.info(f"SCS-UPB-01 - Uploading blob '{container_name}'.'")
        container_client = self.blob_service_client.get_container_client(self.upload_pages_container_name)
        cnt_settings = ContentSettings(content_type=content_type)
        container_client.upload_blob(name=container_name, data=data, content_settings=cnt_settings, overwrite=True)
        self.logging.info('SCS-UPB-02 - Blob uploaded.')

    def upload_corpus_blob(self, container_name, data):
        self.logging.info(f"SCS-UCP-01 - Uploading blob '{container_name}'.'")
        container_client = self.blob_service_client.get_container_client(self.corpus_container_name)
        cnt_settings = ContentSettings(content_type='text/plain')
        container_client.upload_blob(name=container_name, data=data, content_settings=cnt_settings, overwrite=True)
        self.logging.info('SCS-UCP-02 - Blob uploaded.')

    def delete_blob(self, container_name, blob_name):
        self.logging.info(f"SCS-DB-01 - Deleting blob '{container_name}'.'")
        container_client = self.blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)
        
        if blob_client.exists():
            blob_client.delete_blob()
            self.logging.info('SCS-DB-02 - Blob deleted.')
        else:
            self.logging.error(f"SCS-DB-03 - Blob '{blob_name}' doesn't exist in container '{container_name}'.")
        
    def delete_blobs_in_folder(self, container_name, folder_name):
        self.logging.info("SCS-DBF-01 - Deleting blobs in folder +"+folder_name+".")

        container_client = self.blob_service_client.get_container_client(container_name)
        blobs = container_client.list_blobs(name_starts_with=folder_name+"/")

        for blob in blobs:
            blob_client = container_client.get_blob_client(blob.name)
            if blob_client.exists():
                blob_client.delete_blob()
                self.logging.info(f"SCS-DBF-02 - Blob '{blob.name}' deleted.")
            else:
                self.logging.error(f"SCS-DBF-03 - Blob '{blob.name}' doesn't exist in container '{container_name}'.")

        self.logging.info(f"SCS-DBF-03 - Blobs in folder '{folder_name}' deleted in container '{container_name}'.")