#install the lib https://python.langchain.com/v0.1/docs/integrations/llms/bedrock/
#pip install -U langchain-aws
#pip install anthropic
#1 import the ConversationSummaryBufferMemory, ConversationChain, ChatBedrock (BedrockChat) Langchain Modules
from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryBufferMemory
from langchain_aws import ChatBedrock
#2a Write a function for invoking model- client connection with Bedrock with profile, model_id & Inference params- model_kwargs
# this is the set up the LLM model
def demo_chatbot():
    demo_llm=ChatBedrock(
       model_id='anthropic.claude-v2:1',
       credentials_profile_name='ko-engineer',
       region_name='us-east-1',
       model_kwargs= {
           "max_tokens": 1000,
           "temperature": 0.1,
           "top_p": 0.9,
           "stop_sequences": ["\n\nHuman:"]} )
    return demo_llm
#2b Test out the LLM with Predict method instead use invoke method
#     return demo_llm.invoke(input_text)
# response=demo_chatbot(input_text="Hi, what is the temperature in new york in January?")
# print(response)

#3 Create a Function for  ConversationSummaryBufferMemory  (llm and max token limit)
# set up the memory and link it to the LLM model
def demo_memory():
    llm_data=demo_chatbot()
    memory=ConversationSummaryBufferMemory(llm=llm_data,max_token_limit=1000)
    return memory

#4 Create a Function for Conversation Chain - Input text + Memory
def demo_conversation(input_text,memory):
    llm_chain_bot=demo_chatbot()
    #verbose is to have a insight of what happened internally. in Production, should be set up as False
    llm_conversation=ConversationChain(llm=llm_chain_bot,memory=memory,verbose=True)
    chat_reply=llm_conversation.invoke(input_text)
    return chat_reply['response']
