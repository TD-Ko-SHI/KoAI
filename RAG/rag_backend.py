# this is the back-end of the app.
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
#from langchain_community.embeddings import BedrockEmbeddings
from langchain_aws import BedrockEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.indexes import VectorstoreIndexCreator
from langchain_community.llms import Bedrock

# Global variable to hold the database index
db_index = None

# load the data, split it, embed, store into vector db and create the index
def load_pdf_and_create_index(pdf_url):
    """
    Load a PDF from the provided URL, process it, and create an index.

    Parameters:
    pdf_url (str): The URL of the PDF to load.

    Returns:
    db_index: The vector database index created from the PDF.
    """
    # Load the data with PyPDFLoader using the provided URL
    data_load = PyPDFLoader(pdf_url)
    #Split the Text based on Character, Tokens etc. - Recursively split by character - ["\n\n", "\n", " ", ""]
    data_split=RecursiveCharacterTextSplitter(separators=["\n\n", "\n", " ", ""], chunk_size=100,chunk_overlap=10)
    #Create a client for the embeddings
    data_embeddings=BedrockEmbeddings(
    credentials_profile_name= 'ko-engineer',
    region_name='us-east-1',
    model_id='amazon.titan-embed-text-v1')
    #Use facebook FAISS vector DB to store Embeddings and Index for Search - VectorstoreIndexCreator
    data_index=VectorstoreIndexCreator(
        text_splitter=data_split,
        embedding=data_embeddings,
        vectorstore_cls=FAISS)
    #Create index for HR Policy Document
    db_index=data_index.from_loaders([data_load])
    return db_index

#Write a function to connect to Bedrock Foundation Model - Claude Foundation Model
def create_llm():
    llm=Bedrock(
        credentials_profile_name='ko-engineer',
        region_name='us-east-1',
        model_id='anthropic.claude-v2',
        model_kwargs={
        "max_tokens_to_sample":5000,
        "temperature": 0.1,
        "top_p": 0.9})
    return llm
#Write a function which searches the user prompt, searches the best match from Vector DB and sends both to LLM.
def get_rag_response(index,question):
    rag_llm=create_llm()
    hr_rag_query=index.query(question=question,llm=rag_llm)
    return hr_rag_query

# Function to clear the loaded PDF data
def clear_pdf_data():
    """
    Clear the loaded PDF data, embeddings, and database index.
    """
    global db_index
    db_index = None  # Reset the database index
    # Additional cleanup can be done here if needed
    print("PDF data cleared successfully.")