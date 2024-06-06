import pymongo
from models.IndexStatus import IndexStatus
from services.Logger import Logger

class CosmosRepository:
    def __init__(self, connection_string, database_name):
        self.logging = Logger()
        self.client = pymongo.MongoClient(connection_string)
        self.db = self.client[database_name]
        if database_name not in self.client.list_database_names():
            self.logging.error("CDB-1-INIT - Database '{}' not found.".format(database_name))
            raise Exception("Database '{}' not found.".format(database_name))
        else:
            self.logging.info("CDB-2-INIT - Using database: '{}'.\n".format(database_name))
        self.logging.info("CDB-3-INIT - Connected to database: '{}'.\n".format(database_name))

    def update(self, collectionName, item_id, updated_data):
        collection = self.db.get_collection(collectionName)
        result = collection.update_one({"id": item_id}, {"$set": updated_data})
        return result.modified_count
    
    def update_document_page_async(self, collectionName, item_id, documentKBPage):
        collection = self.db.get_collection(collectionName)
        filter = {"id": item_id}
        update = {"$push": {"documentPages": documentKBPage}}
        update_result = collection.update_one(filter, update)
        return update_result.modified_count != 0
    
    def update_document_index_completion(self, collectionName, item_id, indexCompletionDate):
        collection = self.db.get_collection(collectionName)
        filter = {"id": item_id}
        update = {"$set": {"indexStatus": IndexStatus.INDEXED.value, "indexCompletionDate": indexCompletionDate}}
        update_result = collection.update_one(filter, update)
        return update_result.modified_count != 0