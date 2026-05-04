import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
#from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.chat_models import init_chat_model

from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(current_dir, "..", "..", ".secrets")

load_dotenv(dotenv_path=dotenv_path)
#load_dotenv(dotenv_path="../.secrets")

# RAG Sources
#data_path = "../data/travel_guide.txt"
#chroma_path = "chroma_db"

data_path = os.path.normpath(os.path.join(current_dir, "..", "data", "travel_guides.txt"))
chroma_path = os.path.normpath(os.path.join(current_dir, "..", "chroma_db"))

gateway_kwargs = {
    "base_url": 'https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1', 
    "api_key": 'any value',
    "default_headers": {"x-api-key": os.getenv('API_GATEWAY_KEY')}
}

# Initializing a chat model in LangChain
model = init_chat_model(
    model="gpt-4o-mini",
    model_provider="openai",
    temperature=0.7,
    **gateway_kwargs
)

embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    **gateway_kwargs
)

# Load and split documents
def load_documents():
    loader = TextLoader(data_path)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        length_function=len
    )
    return splitter.split_documents(documents)

# Create or load db
def get_vector_db():
    if os.path.exists(chroma_path):
        return Chroma(
            collection_name="travel_guides", 
            embedding_function=embedding_model, 
            persist_directory=chroma_path)
    else:
        documents = load_documents()
        db = Chroma.from_documents(
            documents=documents, 
            embedding=embedding_model, 
            collection_name="travel_guides", 
            persist_directory=chroma_path)
        return db

# Main RAG function

def query_travel_info(user_input: str) -> str:
    # This function will query the travel information for the given destination
    db = get_vector_db()

    results = db.similarity_search(user_input, k=5)

    context = "\n\n".join([result.page_content for result in results])

    prompt = f"""
    You are a travel assistant. 
    Use the following context to answer the question about the destination. 
    If the information is not available in the context, say that the information 
    is unavailable. If the [DATABASE CONTEXT] does not contain the specific answer (e.g., historical climate, 
    specific dates, or deep history), use your own internal knowledge to provide 
    a factual and helpful response. Always maintain a helpful, friendly and professional tone.
    Do not provide information for these topics: cats, dogs, horoscope, zodiac, taylor swift. If the question is about these topics, respond with 
    "Sorry, I cannot discuss that topic. Let's plan your trip to Canada instead!".
    

    Context: {context}

    Question: {user_input}

    Answer in a helpful and concise manner.

    """
    response = model.invoke(prompt)

    return response.content