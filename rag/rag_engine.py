import chromadb
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, load_index_from_storage
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
        
        # Inicializar ChromaDB com caminho temporário
        db = chromadb.PersistentClient(path="db_chroma")
        chroma_collection = db.get_or_create_collection("ihc_collection")
        
        # Configurar vector store
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Carregar documentos (ajuste o caminho conforme necessário)
        documents = SimpleDirectoryReader("./arquivosFormatados").load_data()

        # Criar índice
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            show_progress=True
        )
        
        return index.as_query_engine()
        
    except Exception as e:
        st.error(f"Erro na inicialização do sistema: {str(e)}")
        return None
