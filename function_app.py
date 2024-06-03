import json
import azure.functions as func
from services.Logger import Logger
from builders.MessageBuilder import MessageBuilder
from dotenv import load_dotenv

from processors.ProcessorBuilder import ProcessorBuilder

app = func.FunctionApp()

@app.queue_trigger(arg_name="azqueue", queue_name="original-docs-action-received-py",
                               connection="AzureWebJobsStorage") 
async def ActionReceivedFunc(azqueue: func.QueueMessage):
    load_dotenv()
    logging = Logger()
    logging.info('ARF-01 - Receiving a new queue message from queue.')

    try:
        az_message = azqueue.get_body().decode('utf-8')
        logging.info('ARF-02 - Decoding message: ' + az_message)
        az_message_dict = json.loads(az_message)
        message = MessageBuilder(az_message_dict).build()

        logging.info('ARF-03 -Building processor')
        processor = ProcessorBuilder().build(
            message=message
        )

        logging.info('ARF-04 - Processing message')
        await processor.process()


    except Exception as e:
        raise e
    
    # Listen queue and define if action is index or delete OK

    # Test if is PDF or DOC

    # Download the file

    # Check if the search index already exists or not

    # Create the index

    # Create pages container

    # Add metadata on cosmos

    # Add corpus

    # After sections created it needs indexing and embbeding

    # TEST:
#     {
#   "action": "index",
#   "fileId": "73606be1-397e-4e3c-90c6-79a166ca821f",
#   "storageFilePath": "manualsoperations/counter/B3 Trading Rules.pdf",
#   "fileName": "B3 Trading Rules.pdf",
#   "originalFileFormat": "pdf",
#   "theme": "manualsoperations",
#   "subtheme": "counter",
#   "language": "eng"
# }