import os
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

from exceptions.StorageContainerServiceExceptions import BlobFileDoesntExistsError
from services.Logger import Logger


class StorageContainerService:

    def __init__(self):
        self.download_container_name = os.getenv('STORAGE_CONTAINER_DOWNLOAD_CONTAINER')
        self.logging = Logger()
        run_local = os.getenv('RUN_LOCAL', False)
        self.logging.info('SCS-INIT-01 - Initializing Storage Container Service')
        if run_local:
            self.logging.info('SCS-INIT-02 - Running locally with connection string')
            self.blob_service_client = BlobServiceClient.from_connection_string(os.getenv('STORAGE_CONTAINER_CONNECTION_STRING'))
        else:
            self.logging.info('SCS-INIT-02 - Running in the serve with Default Azure Credentials')
            self.blob_service_client = BlobServiceClient(account_url=os.getenv('AZURE_STORAGE_ACCOUNT_URL'), credential=DefaultAzureCredential())

    def download_blob(self, blob_name):
        self.logging.info('SCS-DB-01 - Download blob method called')
        try:
            self.logging.info('SCS-DB-02 - Getting blob')
            
            blob_client = self.blob_service_client.get_blob_client(container=self.download_container_name, blob=blob_name)
            if not blob_client.exists():
                self.logging.error(f"SCS-DB-03 - Blob doenst exists in container.")
                raise BlobFileDoesntExistsError()
            self.logging.info('SCS-DB-04 - Blob downloaded with success.')
            return blob_client.download_blob()   
        except Exception as e:
            self.logging.error(f"SCS-DB-03 - Error on downloading blob: {e}")
            raise e
