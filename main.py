from dotenv import load_dotenv
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.agent import ReActAgent
from llama_index.llms.openai import OpenAI
from llama_index.core import VectorStoreIndex
from vectorstore import build_vectorstore
from note_engine import note_engine
from datetime import datetime
import streamlit as st
import chromadb
import os
import tempfile
import uuid


st.set_page_config(layout="wide")   # for streamlit full screen


# to load api key from .env file
load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if OPENAI_API_KEY is None:
    st.error("API key is missing")





# 1) Streamlit build vectorstore

st.title("Document Assistant")

# File Upload
st.subheader("Upload Your Files")
uploaded_files = st.file_uploader("Upload PDF", type=["pdf"], accept_multiple_files=True)



# Process Files
if st.button("Build VectorStore"):
    with st.spinner("Processing files..."):
        with tempfile.TemporaryDirectory() as temp_dir:  # saves uploaded files temporarily in the temp_dir; automatically deletes after exiting this block
            for file in uploaded_files:
                temp_path = os.path.join(temp_dir, file.name)
                with open(temp_path, "wb") as f:
                    f.write(file.read())

            collection_name = f"documents_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"    # Generate unique collection name with current date, time and id

            if "collection_names" not in st.session_state:          # to store collection name in session state
                st.session_state["collection_names"] = []
            st.session_state["collection_names"].append(collection_name)

            build_vectorstore(temp_dir, collection_name, OPENAI_API_KEY)   # Temporary folder and files are deleted here automatically because block ends

        
    st.success(f"VectorStore built successfull: {collection_name}")






# 2) Streamlit query vectorstore

if "collection_names" in st.session_state:

    # get the latest collection_name from session state
    collection_name = st.session_state["collection_names"][-1]

    # define embedding function
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-base-en-v1.5")

    # load vectorstore from disk (which was created in vectorstore.py)
    db2 = chromadb.PersistentClient(path="chroma_db")
    chroma_collection = db2.get_or_create_collection(collection_name)

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(
        vector_store,
        embed_model=embed_model,
    )





    # Query Data from the persisted index (vectorstore)
    query_engine = index.as_query_engine()

    vectorstore_engine = QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="document_search",
            description="Search for relevant information in the vectorstore"
        ),
    )

    # Toolbox for the agent
    tools = [
        note_engine,
        vectorstore_engine
    ]

    # Giving the agent the context for its role
    context = """Purpose: The primary role of this agent is to assist users by providing accurate 
                information about truck load transport concerns based on the data contained in vectorstore. 
                If the document doesn't provide enough information he can still give concrete advice but indicate clearly that information is not based on the document!
                He has to give CONCRETE and CONCISE straight forward answers! No generic answers!
                """


    # Activate the agent
    llm = OpenAI(model="gpt-4o-mini")
    agent = ReActAgent.from_tools(tools, llm = llm, verbose = True, context = context)      # sets everything up






    user_prompt = st.text_input("Enter a prompt", "")              # giving agent instructions

    if st.button("Submit") and user_prompt:
        with st.spinner("Processing..."):
            result = agent.query(user_prompt)
            response_text = result.response if hasattr(result, 'response') else result

        st.write("**Result:**")
        st.write(response_text)
