import os
import nltk
import tempfile
from pathlib import Path
import streamlit as st

# Configurar diretórios temporários com permissão de escrita
temp_dir = Path(tempfile.mkdtemp())

# Configurar caminhos para NLTK e ChromaDB dentro do diretório temporário
nltk_data_dir = temp_dir / "nltk_data"
os.environ["NLTK_DATA"] = str(nltk_data_dir)
os.makedirs(nltk_data_dir, exist_ok=True)

chroma_db_dir = temp_dir / "chroma_db"
os.makedirs(chroma_db_dir, exist_ok=True)

# Configurar cache do tiktoken
tiktoken_cache_dir = temp_dir / "tiktoken_cache"
os.environ["TIKTOKEN_CACHE_DIR"] = str(tiktoken_cache_dir)
os.makedirs(tiktoken_cache_dir, exist_ok=True)

# Baixar recursos do NLTK
nltk.download('stopwords', download_dir=nltk_data_dir, quiet=True)
nltk.download('punkt', download_dir=nltk_data_dir, quiet=True)
nltk.download('averaged_perceptron_tagger', download_dir=nltk_data_dir, quiet=True)
nltk.download('wordnet', download_dir=nltk_data_dir, quiet=True)

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
        db = chromadb.PersistentClient(path=str(chroma_db_dir))
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
        
        return index.as_query_engine()
    except Exception as e:
        st.error(f"Erro na inicialização do sistema: {str(e)}")
        return None
