import pymongo
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
