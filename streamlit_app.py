__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
from auth.firebase_auth import initialize_firebase_admin
from auth.pyrebase_auth import initialize_pyrebase
from auth.auth_interface import show_auth_page
from chat.chat_interface import (
    show_chat_interface, 
    load_chat_messages_from_firestore,
    create_new_chat_in_firestore, 
    list_user_chats_from_firestore
)
# from rag.rag_engine import initialize_system
import strftime
from utils.time_utils import get_brasilia_time
import streamlit.components.v1 as components

def handle_chats(firestore_db, auth):
    """Gerencia a interface de chats e histórico"""
    
    # Verificar se é a primeira vez que está acessando após o login
    if "first_access" not in st.session_state:
        # Marca como primeiro acesso
        st.session_state.first_access = True
        
        # Sempre cria um novo chat ao fazer login
        new_chat_title = f"Chat {get_brasilia_time().strftime('%d/%m/%Y %H:%M')}"
        new_chat_id = create_new_chat_in_firestore(firestore_db, st.session_state.user_id, new_chat_title)
        st.session_state.current_chat_id = new_chat_id
        
        # Inicializa mensagens vazias para o novo chat
        st.session_state.messages = []
        
        # Lista todos os chats incluindo o recém-criado
        st.session_state.chats = list_user_chats_from_firestore(firestore_db, st.session_state.user_id)
    else:
        # Inicializar o estado da sessão para chats se não existir
        if "chats" not in st.session_state:
            st.session_state.chats = list_user_chats_from_firestore(firestore_db, st.session_state.user_id)
        
        if "current_chat_id" not in st.session_state:
            st.session_state.current_chat_id = None
        
        if "messages" not in st.session_state:
            st.session_state.messages = []
    
    # Sidebar para gerenciar chats
    with st.sidebar:
        st.title("💬 Meus Chats")
        
        # Botão para novo chat com ícone de mais
        if st.button("➕ Novo Chat"):
            new_chat_title = f"Chat {get_brasilia_time().strftime('%d/%m/%Y %H:%M')}"
            new_chat_id = create_new_chat_in_firestore(firestore_db, st.session_state.user_id, new_chat_title)
            
            # Atualizar o estado
            st.session_state.current_chat_id = new_chat_id
            st.session_state.chats = list_user_chats_from_firestore(firestore_db, st.session_state.user_id)
            st.session_state.messages = []
            st.rerun()
        
        # Lista de chats existentes com ícone de mensagem
        st.divider()
        for chat_id, chat_data in st.session_state.chats.items():
            # Destacar o chat atual
            is_current = chat_id == st.session_state.current_chat_id
            button_label = f"{chat_data['title']}" if is_current else f"{chat_data['title']}"
            
            if st.button(button_label, key=f"chat_{chat_id}"):
                st.session_state.current_chat_id = chat_id
                st.session_state.messages = load_chat_messages_from_firestore(firestore_db, chat_id)
                st.rerun()
        
        # Adicionar uma divisão antes do perfil do usuário
        st.divider()
        
        # Seção para mostrar o email do usuário e opção de logout
        if "user_email" in st.session_state:
            # Criando um container para o dropdown
            user_container = st.container()
            
            # Criando um expander para simular um dropdown
            with user_container.expander(f"👤 {st.session_state.user_email}"):
                if st.button("🚪 Sair"):
                    # Lógica para logout
                    try:
                        auth.current_user = None  # Limpar o usuário atual no auth
                        for key in list(st.session_state.keys()):
                            del st.session_state[key]  # Limpar todos os estados
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao fazer logout: {str(e)}")

def main():
    try:
        # Inicializar Firebase
        firestore_db = initialize_firebase_admin()
        pyrebase_app = initialize_pyrebase()
        
        if pyrebase_app:
            auth = pyrebase_app.auth()
        
        st.set_page_config(
            page_title="IAHC ChatBot",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="auto"
        )
        
        # Verificar autenticação
        if "user_id" not in st.session_state or not st.session_state.user_id:
            show_auth_page(auth, firestore_db)
        else:
            handle_chats(firestore_db, auth)
            
            # Inicializar e mostrar interface do chat
            # query_engine = initialize_system()
            # Stub temporário para query_engine
            class QueryEngineStub:
                def query(self, text):
                    return "Informações de contexto para a consulta sobre IHC."
            
            query_engine = QueryEngineStub()
            
            show_chat_interface(
                query_engine, 
                firestore_db, 
                st.session_state.current_chat_id, 
                st.session_state.messages
            )
    except Exception as e:
        st.error(f"Erro durante a execução: {str(e)}")

if __name__ == "__main__":
    main()
