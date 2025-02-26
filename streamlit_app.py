__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
from auth.firebase_auth import initialize_firebase_admin
from auth.pyrebase_auth import initialize_pyrebase
from chat.chat_interface import show_chat_interface
from rag.rag_engine import initialize_system
from utils.time_utils import get_brasilia_time

def main():
    try:
        db_admin = initialize_firebase_admin()
        pyrebase_app = initialize_pyrebase()
        
        if pyrebase_app:
            auth = pyrebase_app.auth()
            db = pyrebase_app.database()
        
        st.set_page_config(
            page_title="IAHC Chatbot",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="auto"
        )
        
        if "user_id" not in st.session_state or not st.session_state.user_id:
            show_auth_page()
        else:
            handle_chats()
            #query_engine = initialize_system()
            ##show_chat_interface(query_engine, st.session_state.current_chat_id, st.session_state.messages)
    except Exception as e:
        st.error(f"Erro durante a execução: {str(e)}")

if __name__ == "__main__":
    main()
