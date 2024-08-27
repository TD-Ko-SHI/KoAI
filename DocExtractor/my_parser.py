from langchain.chains import create_extraction_chain_pydantic
from cv_class import Individual
from langchain_community.document_loaders import PyPDFLoader
# from langchain_anthropic import ChatAnthropic
from langchain_aws import ChatBedrock

# Load and split the PDF document
pdf_loader = PyPDFLoader("/Users/ko.shi/Projects/hang-shi/DocExtractor/openresume-resume.pdf")
pages = pdf_loader.load_and_split()

# # Iterate over the list of Document objects
# for document in pages:
#     # Access metadata
#     source = document.metadata.get('source')
#     page_number = document.metadata.get('page')

#     # Access page content
#     content = document.page_content

#     # Print or process the information
#     print(f"Source: {source}, Page: {page_number}")
#     print("Content:")
#     print(content)
#     print("\n" + "="*40 + "\n")

llm=ChatBedrock(
    model_id='anthropic.claude-v2:1',
    credentials_profile_name='ko-engineer',
    region_name='us-east-1',
    model_kwargs= {
        "max_tokens": 1000,
        "temperature": 0,
        "top_p": 0.9,
        "stop_sequences": ["\n\nHuman:"]} )

# Create the extraction chain
chain = create_extraction_chain_pydantic(pydantic_schema=Individual, llm=llm)

# Run the chain with the first page content
result = chain.run([pages[0].page_content])
print(result)