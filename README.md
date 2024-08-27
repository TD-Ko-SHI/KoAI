# KoAI
Welcome to KoAI
Choose the right virtual evn, specify the correct interpreter in VSCode By command+shift+p
To run the front-end, run the command streamlit run XXX.py, the browswer will be launched \
Make sure you use the right AWS profile with permission and region. some models are only available in some partitular region right now. 

## BedrockChatBox
It is a simple app which showcases how to leverage the AWS Bedrock and Langchain to build conversational chain, memory-enabled chatbot. 

## RAG
This is a python application with front-end and back-end. It is using the streamlit as the front-end and langchain, FAISS, AWS Bedrock as the back-end. You can provide the URL of the pdf and start to ask questions.
Need to install the following in advance.
pip3 install flask-sqlalchemy
pip install -U langchain-community
pip install faiss-gpu (for CUDA supported GPU)
pip install faiss-cpu (depending on Python version).

## Agent
this is built by using Bedrock Agent, lambda function and knowledgebase. 
The Agent serves as orchestrating part to process the prompt
The Agent connects to the dynamodb in which the user-information is being stores.
The Agent also links to the Knowledge Base to have addionional explanations. 
The Agent consists of "OpenAPI Schema" ApllicationStatus.yaml in this project 
  and lambda function as a whole action group.

## DocExtractor
This application is using Pydantic as the parsing lib to extract contenxts from PDF etc documentations and return the structured results for 3rd party API/Applications. Pydantic provides the control and flexibility in content-extracting process.

## NotionTextSpeech
This is a application to learn French words in Notion. we leverage the AWS BedRock as the Text Generation Tooling and Polly to convert the generated sample sentence into mp3 audio. We store the audio in S3 and insert the record into DynamoDB. 