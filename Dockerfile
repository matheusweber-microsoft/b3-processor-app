# For more information, please refer to https://aka.ms/vscode-docker-python
FROM mcr.microsoft.com/azure-functions/python:4-python3.10-slim

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true \
    AzureWebJobsFeatureFlags=EnableWorkerIndexing 

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY . /home/site/wwwroot
