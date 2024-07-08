# Here goes the agent tools
import os
import csv
import json
import requests
from typing import Tuple
from dotenv import load_dotenv
from prompts import general_info_prompt, services_info_prompt
from typing_extensions import Dict
from langchain.tools import BaseTool, StructuredTool, Tool, tool

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

url = "https://api.calendly.com"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.getenv("CALENDLY_API_KEY")}"
}

def process_general_info() -> list:
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import CharacterTextSplitter

    loader = PyPDFLoader("data/company_info.pdf")
    pages = loader.load()
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len
    )
    docs = text_splitter.split_documents(pages)

    return docs

def process_services_info() -> list:
    services = []
    with open('data/services_pricing_table.csv', 'r') as file:
        reader = csv.reader(file)
        headers = next(reader)  # Get the header row
        for row in reader:
            service = {}
            splitted_row = row[0].split(";")
            service["service"] = splitted_row[0]
            service["cost"] = splitted_row[1]
            service["time"] = splitted_row[2]
            services.append(service)

    return services

@tool("company_general_info", return_direct=True)
def get_company_general_info(query: str) -> list:
    """Process user query and retrieve answer with general information about the company, such as it's story, contact, address and open hours."""
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.vectorstores import FAISS

    docs = process_general_info()
    faiss_index = FAISS.from_documents(docs, OpenAIEmbeddings())
    similarDocs = faiss_index.similarity_search(query, k=3)

    return similarDocs

@tool("services_info", return_direct=True)
def get_services_information(query: str) -> list:
    """Answer questions related to the services done by the business. The information could be the type of service, how much it cost and the time needed to complete the service. You could be asked about multiple services in the same query."""
    from langchain_openai import OpenAIEmbeddings
    from langchain.docstore.document import Document
    from langchain_community.vectorstores import FAISS

    services = process_services_info()
    documents = [Document(page_content=str(service)) for service in services]
    faiss_index = FAISS.from_documents(documents, OpenAIEmbeddings())

    similarServices = faiss_index.similarity_search(query, k=10)

    return similarServices

@tool("service_availability", return_direct=True)
def get_availability_for_service(service: str, start_time: str, end_time: str):
    """Consult external platform to check available slots to do the service withing a date range.
    Receive the type of service, the start date and the end date of the request. Dates should come in the format YYYY-MM-DDT00:00:00:000000Z."""
    querystring = {"event_type":f"https://api.calendly.com/event_types/38d3aad8-d16a-4035-83b0-03e9003c87fb","start_time":{start_time},"end_time":{end_time}}

    response = requests.request("GET", f"{url}/event_type_available_times", headers=headers, params=querystring)
    json_response = response.json()
    if "collection" not in json_response:
        return []
    return ([date["start_time"] for date in json_response["collection"]],[])

# @tool("book_appoitment", return_direct=True)
# def book_service_appoitment(service: str, start_time: str):
#     """Book an appointment for a service in a specific date.
#     Receive the type of service and the start date of the appoitment. Date should come in the format YYYY-MM-DDT00:00:00:000000Z."""
#     querystring = {"event_type":f"https://api.calendly.com/event_types/38d3aad8-d16a-4035-83b0-03e9003c87fb","start_time":{start_time},"end_time":{end_time}}

#     response = requests.request("GET", f"{url}/event_type_available_times", headers=headers, params=querystring)
#     json_response = response.json()
#     if "collection" not in json_response:
#         return []
#     return ([date["start_time"] for date in json_response["collection"]],[])
