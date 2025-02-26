import os
import nltk

# Crie um diretório local para os dados NLTK
nltk_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nltk_data")
os.makedirs(nltk_data_dir, exist_ok=True)
nltk.data.path.append(nltk_data_dir)

# Baixe todos os pacotes comumente usados pelo LlamaIndex
resources_to_download = [
    "stopwords",
    "punkt",
    "punkt_tab",
    "averaged_perceptron_tagger",
    "wordnet"
]

for resource in resources_to_download:
    try:
        nltk.download(resource, download_dir=nltk_data_dir, quiet=True)
    except Exception as e:
        print(f"Aviso: não foi possível baixar o recurso NLTK '{resource}': {str(e)}")

import chromadb
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, load_index_from_storage
from llama_index.vector_stores.chroma.base import ChromaVectorStore
from llama_index.core import StorageContext
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import streamlit as st

def get_or_create_index(documents, persist_dir="./storage"):
    if os.path.exists(persist_dir):
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        index = load_index_from_storage(storage_context)
    else:
        index = VectorStoreIndex.from_documents(documents, show_progress=True)
        index.storage_context.persist(persist_dir=persist_dir)
    return index

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
        
        # Usar a função get_or_create_index para criar ou carregar o índice
        index = get_or_create_index(documents, persist_dir="./storage")
        
        return index.as_query_engine()
    except Exception as e:
        st.error(f"Erro na inicialização do sistema: {str(e)}")
        return None
