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
from utils.time_utils import get_brasilia_time

def handle_chats(firestore_db):
    """Gerencia a interface de chats e histórico"""
    
    # Inicializar o estado da sessão para chats
    if "chats" not in st.session_state:
        st.session_state.chats = list_user_chats_from_firestore(firestore_db, st.session_state.user_id)
    
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Sidebar para gerenciar chats
    with st.sidebar:
        st.title("Meus Chats")
        
        # Botão para novo chat
        if st.button("Novo Chat"):
            new_chat_title = f"Chat {len(st.session_state.chats) + 1}"
            new_chat_id = create_new_chat_in_firestore(firestore_db, st.session_state.user_id, new_chat_title)
            
            # Atualizar o estado
            st.session_state.current_chat_id = new_chat_id
            st.session_state.chats = list_user_chats_from_firestore(firestore_db, st.session_state.user_id)
            st.session_state.messages = []
            st.rerun()
        
        # Lista de chats existentes
        st.divider()
        for chat_id, chat_data in st.session_state.chats.items():
            if st.button(f"{chat_data['title']}", key=f"chat_{chat_id}"):
                st.session_state.current_chat_id = chat_id
                st.session_state.messages = load_chat_messages_from_firestore(firestore_db, chat_id)
                st.rerun()

def main():
    try:
        # Inicializar Firebase
        firestore_db = initialize_firebase_admin()
        pyrebase_app = initialize_pyrebase()
        
        if pyrebase_app:
            auth = pyrebase_app.auth()
        
        st.set_page_config(
            page_title="IAHC Chatbot",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="auto"
        )
        
        # Verificar autenticação
        if "user_id" not in st.session_state or not st.session_state.user_id:
            show_auth_page(auth, firestore_db)
        else:
            handle_chats(firestore_db)
            
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

# Função para atualizar a interface auth_interface.py
def update_auth_interface():
    """
    Código para auth_interface.py - removi o login com Google
    """
    import streamlit as st
    from auth.auth_utils import login_with_email, register_user, reset_password

    def show_auth_page(auth, firestore_db):
        """Mostra a página de autenticação"""
        st.title("Bem-vindo ao Chatbot Especialista em IHC")
        
        tab = st.tabs(["Login", "Cadastro", "Recuperar Senha"])
        
        with tab[1]:
            # Formulário de login
            with st.form("login_form"):
                email = st.text_input("E-mail", key="login_email")
                password = st.text_input("Senha", type="password", key="login_password")
                submit_login = st.form_submit_button("Entrar")
                
                if submit_login:
                    if email and password:
                        user, error = login_with_email(auth, email, password)
                        if user:
                            st.session_state.user_id = user['localId']
                            st.session_state.user_info = user
                            st.rerun()
                        else:
                            st.error(error)
                    else:
                        st.warning("Por favor, preencha todos os campos.")
        
        with tab[2]:
            # Formulário de cadastro
            with st.form("register_form"):
                name = st.text_input("Nome", key="register_name")
                email = st.text_input("E-mail", key="register_email")
                password = st.text_input("Senha", type="password", key="register_password")
                confirm_password = st.text_input("Confirmar Senha", type="password", key="confirm_password")
                submit_register = st.form_submit_button("Cadastrar")
                
                if submit_register:
                    if name and email and password and confirm_password:
                        if password == confirm_password:
                            user, error = register_user(auth, firestore_db, email, password, name)
                            if user:
                                st.success("Cadastro realizado com sucesso! Faça login.")
                                tab1.active = True  # Vai para a tab de login
                            else:
                                st.error(error)
                        else:
                            st.error("As senhas não coincidem.")
                    else:
                        st.warning("Por favor, preencha todos os campos.")
        
        with tab[3]:
            # Formulário de recuperação de senha
            with st.form("reset_password_form"):
                email = st.text_input("E-mail", key="reset_email")
                submit_reset = st.form_submit_button("Recuperar Senha")
                
                if submit_reset:
                    if email:
                        success, message = reset_password(auth, email)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                    else:
                        st.warning("Por favor, insira seu e-mail.")

if __name__ == "__main__":
    main()
