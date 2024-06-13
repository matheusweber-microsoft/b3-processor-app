import logging
import os
from opencensus.ext.azure.log_exporter import AzureLogHandler


class Logger:
    def __init__(self):
        self.logger = logging.getLogger()
        if not self.logger.handlers:
            log_level = os.getenv('LOG_LEVEL', 'INFO')
            self.logger.setLevel(getattr(logging, log_level))
            
            # Callback function to add os_type: linux to span properties
            def callback_function(envelope):
                envelope.tags['ai.cloud.role'] = 'ingestion-processor'
                return True

            # Azure log handler
            azure_handler = AzureLogHandler(connection_string=os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING'))
            azure_handler.add_telemetry_processor(callback_function)
            formatter = logging.Formatter('%(filename)s - %(levelname)s - %(message)s')
            azure_handler.setFormatter(formatter)
            self.logger.addHandler(azure_handler)

            # Stream handler
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)

    def warning(self, message):
        self.logger.warning(message)
