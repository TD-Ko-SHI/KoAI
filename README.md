# KoAI
Welcome to KoAI
Choose the right virtual evn, specify the correct interpreter in VSCode By command+shift+p
To run the front-end, run the command streamlit run XXX.py, the browswer will be launched \
Make sure you use the right AWS profile with permission and region. some models are only available in some partitular region right now. 

## BedrockChatBox
it is built on the AWS Bedrock, 
## RAG
need to install the following in advance
pip3 install flask-sqlalchemy
pip install -U langchain-community
pip install faiss-gpu (for CUDA supported GPU)
pip install faiss-cpu (depending on Python version).