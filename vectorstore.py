from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import StorageContext
import chromadb
import os


# to load api key from .env file
load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")



def build_vectorstore(files, collection_name, api_key=OPENAI_API_KEY):

    # initializing ChromaDB
    db = chromadb.PersistentClient(path="chroma_db")
    chroma_collection = db.get_or_create_collection(collection_name)


    # define embedding function
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-base-en-v1.5")


    # load documents
    documents = SimpleDirectoryReader(files).load_data()
        

    # create and store vectors
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)


    # building the index
    VectorStoreIndex.from_documents(
        documents, 
        storage_context=storage_context, 
        embed_model=embed_model,
        show_progress=True
    )
