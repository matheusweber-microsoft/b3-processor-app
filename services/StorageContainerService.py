import os
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from io import BytesIO

from exceptions.StorageContainerServiceExceptions import BlobFileDoesntExistsError
from services.Logger import Logger


class StorageContainerService:

    def __init__(self):
        self.download_container_name = os.getenv('STORAGE_CONTAINER_DOWNLOAD_CONTAINER')
        self.logging = Logger()        
        self.logging.info('SCS-INIT-01 - Running in the serve with Default Azure Credentials')
        self.blob_service_client = BlobServiceClient(account_url=os.getenv('STORAGE_CONTAINER_ACCOUNT_URL'), 
                                                     credential=DefaultAzureCredential())

    def download_blob(self, blob_name):
        self.logging.info('SCS-DB-01 - Download blob method called')
        try:
            self.logging.info('SCS-DB-02 - Getting blob')
            
            blob_client = self.blob_service_client.get_blob_client(container=self.download_container_name, 
                                                                   blob=blob_name)
            if not blob_client.exists():
                self.logging.error(f"SCS-DB-03 - Blob doenst exists in container.")
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
