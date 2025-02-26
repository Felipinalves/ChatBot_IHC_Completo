import os
import nltk

# Crie um diretório local para os dados NLTK
nltk_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nltk_data")
os.makedirs(nltk_data_dir, exist_ok=True)
nltk.data.path.append(nltk_data_dir)

# Baixe os stopwords de forma proativa
nltk.download("stopwords", download_dir=nltk_data_dir)

import chromadb
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores.chroma.base import ChromaVectorStore
from llama_index.core import StorageContext
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import streamlit as st

@st.cache_resource(show_spinner=False)
def initialize_system():
    try:
        Settings.embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        Settings.llm = None
        
        db = chromadb.PersistentClient(path="chroma_db")
        chroma_collection = db.get_or_create_collection("quickstart")
        
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        documents = SimpleDirectoryReader("./arquivosFormatados").load_data()
        index = VectorStoreIndex.from_documents(
            documents, 
            storage_context=storage_context,
            show_progress=True
        )
        
        return index.as_query_engine()
    except Exception as e:
        st.error(f"Erro na inicialização do sistema: {str(e)}")
        return None
