import json
import azure.functions as func
import logging
from builders.MessageBuilder import MessageBuilder
from models.Message import Message

app = func.FunctionApp()

@app.queue_trigger(arg_name="azqueue", queue_name="original-docs-action-received-py",
                               connection="AzureWebJobsStorage") 
def ActionReceivedFunc(azqueue: func.QueueMessage):
    try:
        az_message = azqueue.get_body().decode('utf-8')
        az_message_dict = json.loads(az_message)
        print(az_message_dict)

        message = MessageBuilder(az_message_dict).build()
        print(message.to_string())
    except Exception as e:
        raise e
    
    # Listen queue and define if action is index or delete

    # Test if is PDF or DOC

    # Download the file

    # Check if the search index already exists or not

    # Create the index

    # Create pages container

    # Add metadata on cosmos

    # Add corpus

    # After sections created it needs indexing and embbeding