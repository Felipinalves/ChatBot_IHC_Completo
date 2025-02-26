__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import uuid
import datetime
import pytz
import pyrebase
import sys
import json
import os
from functools import wraps
import chromadb
import time
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores.chroma.base import ChromaVectorStore
from llama_index.core import StorageContext
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import google.generativeai as genai


import nltk
nltk.download('stopwords')

# Configurações do Firebase
firebase_config = {
    "apiKey": st.secrets["FIREBASE_API_KEY"],
    "authDomain": st.secrets["FIREBASE_AUTH_DOMAIN"],
    "databaseURL": st.secrets["FIREBASE_DATABASE_URL"],
    "projectId": st.secrets["FIREBASE_PROJECT_ID"],
    "storageBucket": st.secrets["FIREBASE_STORAGE_BUCKET"],
    "messagingSenderId": st.secrets["FIREBASE_MESSAGING_SENDER_ID"],
    "appId": st.secrets["FIREBASE_APP_ID"]
}

# Inicializar Firebase
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
db = firebase.database()

# Configuração da página
st.set_page_config(
    page_title="IAHC Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="auto"
)

# Funções de utilidade
def get_brasilia_time():
    """Retorna data e hora atual no fuso de Brasília como string ISO."""
    brasilia_tz = pytz.timezone('America/Sao_Paulo')
    now = datetime.datetime.now(brasilia_tz)
    return now.isoformat()

# Funções para autenticação Firebase
def login_with_email(email, password):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        return user
    except Exception as e:
        error_json = e.args[1]
        error_dict = json.loads(error_json)
        error_message = error_dict.get('error', {}).get('message', 'Erro desconhecido')
        
        if error_message == 'EMAIL_NOT_FOUND':
            return None, "E-mail não encontrado. Por favor, verifique seu e-mail ou crie uma conta."
        elif error_message == 'INVALID_PASSWORD':
            return None, "Senha incorreta. Por favor, tente novamente."
        else:
            return None, f"Erro ao fazer login: {error_message}"

def login_with_google():
    # No Streamlit, isso geralmente envolve redirecionar para uma página de autenticação do Google
    # e depois voltar para o aplicativo. Isso é um placeholder.
    st.info("Redirecionando para autenticação Google...")
    auth_url = auth.generate_sign_in_with_email_link(
        st.session_state.email, firebase_config["authDomain"])
    st.markdown(f"[Clique aqui para fazer login com o Google]({auth_url})")

def register_user(email, password, name):
    try:
        user = auth.create_user_with_email_and_password(email, password)
        # Adicionar informações do usuário ao banco de dados
        user_data = {
            "name": name,
            "email": email,
            "created_at": get_brasilia_time(),
            "photo_url": ""
        }
        db.child("users").child(user['localId']).set(user_data)
        return user, None
    except Exception as e:
        error_json = e.args[1]
        error_dict = json.loads(error_json)
        error_message = error_dict.get('error', {}).get('message', 'Erro desconhecido')
        
        if error_message == 'EMAIL_EXISTS':
            return None, "Este e-mail já está em uso. Tente fazer login ou recuperar sua senha."
        elif error_message == 'WEAK_PASSWORD':
            return None, "Senha fraca. Use pelo menos 6 caracteres."
        else:
            return None, f"Erro ao criar conta: {error_message}"

def reset_password(email):
    try:
        auth.send_password_reset_email(email)
        return True, "E-mail de recuperação enviado. Verifique sua caixa de entrada."
    except Exception as e:
        error_json = e.args[1]
        error_dict = json.loads(error_json)
        error_message = error_dict.get('error', {}).get('message', 'Erro desconhecido')
        
        if error_message == 'EMAIL_NOT_FOUND':
            return False, "E-mail não encontrado. Por favor, verifique seu e-mail ou crie uma conta."
        else:
            return False, f"Erro ao enviar e-mail de recuperação: {error_message}"

def get_user_info(user_id):
    try:
        user_info = db.child("users").child(user_id).get().val()
        return user_info
    except Exception as e:
        st.error(f"Erro ao obter informações do usuário: {str(e)}")
        return None

# Decorator para verificar autenticação
def requires_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in st.session_state or not st.session_state.user_id:
            st.warning("Por favor, faça login para acessar esta página.")
            show_auth_page()
            return None
        return func(*args, **kwargs)
    return wrapper

# Funções de gerenciamento de chats
def save_chat_to_firebase(chat_id, data):
    try:
        if "user_id" in st.session_state and st.session_state.user_id:
            db.child("chats").child(chat_id).set(data, st.session_state.id_token)
            return True
    except Exception as e:
        st.error(f"Erro ao salvar chat: {str(e)}")
    return False

def get_chats_from_firebase():
    try:
        if "user_id" in st.session_state and st.session_state.user_id:
            chats = db.child("chats").order_by_child("user_id").equal_to(st.session_state.user_id).get(st.session_state.id_token)
            if chats.val():
                return chats.val()
        return {}
    except Exception as e:
        st.error(f"Erro ao obter chats: {str(e)}")
        return {}

# Componentes de Interface
def show_auth_page():
    """Exibe a página de autenticação (login, cadastro, recuperação de senha)"""
    
    # Inicializar estados da sessão para autenticação
    if "auth_page" not in st.session_state:
        st.session_state.auth_page = "login"  # login, register, reset
    
    if "email" not in st.session_state:
        st.session_state.email = ""
        
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("IAHC Chatbot 🤖")
        
        # Tabs para diferentes opções de autenticação
        tab1, tab2, tab3 = st.tabs(["Login", "Cadastro", "Recuperar Senha"])
        
        with tab1:
            st.subheader("Login")
            
            email = st.text_input("E-mail", key="login_email")
            password = st.text_input("Senha", type="password", key="login_password")
            
            col_login_btn, col_google_btn = st.columns(2)
            
            with col_login_btn:
                if st.button("Entrar", use_container_width=True):
                    if email and password:
                        user, error = login_with_email(email, password)
                        if user:
                            st.session_state.user_id = user['localId']
                            st.session_state.id_token = user['idToken']
                            st.session_state.refresh_token = user['refreshToken']
                            st.session_state.email = user['email']
                            
                            # Obter informações do usuário
                            user_info = get_user_info(user['localId'])
                            if user_info:
                                st.session_state.user_name = user_info.get('name', 'Usuário')
                                st.session_state.user_photo = user_info.get('photo_url', '')
                            
                            st.success("Login realizado com sucesso!")
                            st.rerun()
                        else:
                            st.error(error)
                    else:
                        st.warning("Por favor, preencha todos os campos.")
            
            with col_google_btn:
                if st.button("Login com Google", use_container_width=True):
                    login_with_google()
                    
        with tab2:
            st.subheader("Criar uma nova conta")
            
            name = st.text_input("Nome completo", key="register_name")
            email = st.text_input("E-mail", key="register_email")
            password = st.text_input("Senha", type="password", key="register_password")
            confirm_password = st.text_input("Confirmar senha", type="password", key="register_confirm_password")
            
            if st.button("Cadastrar", use_container_width=True):
                if name and email and password and confirm_password:
                    if password != confirm_password:
                        st.error("As senhas não coincidem.")
                    else:
                        user, error = register_user(email, password, name)
                        if user:
                            st.session_state.user_id = user['localId']
                            st.session_state.id_token = user['idToken']
                            st.session_state.refresh_token = user['refreshToken']
                            st.session_state.email = user['email']
                            st.session_state.user_name = name
                            
                            st.success("Conta criada com sucesso!")
                            st.rerun()
                        else:
                            st.error(error)
                else:
                    st.warning("Por favor, preencha todos os campos.")
        
        with tab3:
            st.subheader("Recuperar senha")
            
            email = st.text_input("Digite seu e-mail", key="reset_email")
            
            if st.button("Enviar link de recuperação", use_container_width=True):
                if email:
                    success, message = reset_password(email)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.warning("Por favor, digite seu e-mail.")

@requires_auth
def handle_chats():
    """Gerencia a exibição e manipulação dos chats"""
    
    # Inicializar estados de sessão para chats
    if "chats" not in st.session_state:
        st.session_state.chats = {}
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "first_time_flag" not in st.session_state:
        st.session_state.first_time_flag = True
    
    # Obter chats do Firebase se não houver nenhum na sessão
    if not st.session_state.chats:
        firebase_chats = get_chats_from_firebase()
        for chat_id, chat_data in firebase_chats.items():
            st.session_state.chats[chat_id] = {
                "title": chat_data.get("title", "Chat sem título"),
                "created_at": chat_data.get("created_at", ""),
                "updated_at": chat_data.get("updated_at", "")
            }
    
    # Se for a primeira vez que o usuário acessa o app, criar um chat inicial
    if st.session_state.first_time_flag and not st.session_state.chats:
        new_chat_id = str(uuid.uuid4())
        timestamp = get_brasilia_time()
        
        # Criar novo chat no Firebase
        chat_data = {
            "user_id": st.session_state.user_id,
            "title": f"Chat {timestamp}",
            "created_at": timestamp,
            "updated_at": timestamp,
            "messages": [{
                "role": "assistant",
                "content": "Olá! Como posso ajudar você hoje?"
            }]
        }
        
        save_chat_to_firebase(new_chat_id, chat_data)
        
        st.session_state.chats[new_chat_id] = {
            "title": f"Chat {timestamp}",
            "created_at": timestamp,
            "updated_at": timestamp
        }
        st.session_state.current_chat_id = new_chat_id
        st.session_state.messages = [{
            "role": "assistant",
            "content": "Olá! Como posso ajudar você hoje?"
        }]
        st.session_state.first_time_flag = False
    
    # Exibir barra lateral com perfil de usuário e chats
    with st.sidebar:
        # Informações do usuário
        if st.session_state.user_photo:
            st.image(st.session_state.user_photo, width=50)
        
        st.write(f"👤 **{st.session_state.user_name}**")
        st.write(f"📧 {st.session_state.email}")
        
        if st.button("Sair", key="logout_btn"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.divider()
        
        # Título para os chats
        st.title("💬 Meus Chats")
        
        # Botão para novo chat
        if st.button("➕ Novo Chat", use_container_width=True):
            new_chat_id = str(uuid.uuid4())
            timestamp = get_brasilia_time()
            
            # Criar novo chat no Firebase
            chat_data = {
                "user_id": st.session_state.user_id,
                "title": f"Chat {timestamp}",
                "created_at": timestamp,
                "updated_at": timestamp,
                "messages": [{
                    "role": "assistant",
                    "content": "Olá! Como posso ajudar você hoje?"
                }]
            }
            
            save_chat_to_firebase(new_chat_id, chat_data)
            
            st.session_state.chats[new_chat_id] = {
                "title": f"Chat {timestamp}",
                "created_at": timestamp,
                "updated_at": timestamp
            }
            st.session_state.current_chat_id = new_chat_id
            st.session_state.messages = [{
                "role": "assistant",
                "content": "Olá! Como posso ajudar você hoje?"
            }]
            st.rerun()
        
        # Exibir histórico de chats
        st.subheader("Histórico de Chats")
        
        # Ordenar chats por data de criação (mais recentes primeiro)
        sorted_chats = sorted(
            st.session_state.chats.items(),
            key=lambda x: x[1]["created_at"],
            reverse=True
        )
        
        # Exibir botões para cada chat
        for chat_id, chat_info in sorted_chats:
            if st.button(f"{chat_info['title']}", key=f"chat_{chat_id}", use_container_width=True):
                st.session_state.current_chat_id = chat_id
                
                # Obter mensagens do chat do Firebase
                chat_data = db.child("chats").child(chat_id).get(st.session_state.id_token).val()
                if chat_data and "messages" in chat_data:
                    st.session_state.messages = chat_data["messages"]
                else:
                    st.session_state.messages = [{
                        "role": "assistant",
                        "content": "Olá! Como posso te ajudar hoje?"
                    }]
                st.rerun()
        
        # Mensagem informativa se não houver chats
        if not st.session_state.chats:
            st.info("Nenhum chat encontrado. Crie um novo para começar.")

# Inicialização do sistema de RAG
@st.cache_resource(show_spinner=False)
def initialize_system():
    try:
        # Configurar o Gemini
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        
        # Configurar o modelo de embedding
        Settings.embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        Settings.llm = None
        
        # Inicializar ChromaDB
        db = chromadb.PersistentClient(path="chroma_db")
        chroma_collection = db.get_or_create_collection("quickstart")
        
        # Configurar vector store
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Carregar documentos e criar índice
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

def generate_response_with_gemini(prompt, max_retries=3):
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    }
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config
    )
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            if response.text:
                return response.text
            return None
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            st.error(f"Erro ao gerar resposta: {str(e)}")
            return None

@requires_auth
def show_chat_interface():
    """Exibe a interface principal do chatbot"""
    
    # Inicializar o sistema RAG
    query_engine = initialize_system()
    
    if query_engine is None:
        st.error("Não foi possível inicializar o sistema. Por favor, verifique os logs e tente novamente.")
        return
    
    # Título do chat
    chat_id = st.session_state.current_chat_id
    if chat_id and chat_id in st.session_state.chats:
        st.title(f"🤖 {st.session_state.chats[chat_id]['title']}")
    else:
        st.title("Chatbot Especialista em IHC 🤖")
    
    st.info("Este chatbot utiliza RAG (Retrieval Augmented Generation) para fornecer respostas precisas sobre IHC.", icon="ℹ️")
    
    # Exibir histórico de mensagens
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Interface de entrada do chat
    if prompt := st.chat_input("Faça uma pergunta sobre IHC"):
        # Adicionar mensagem do usuário
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Exibir mensagem do usuário
        with st.chat_message("user"):
            st.write(prompt)
        
        # Mostrar indicador de "pensando"
        with st.status("Processando sua pergunta...", expanded=True) as status:
            st.write("Buscando informações relevantes...")
            
            # Recuperar contexto
            context = str(query_engine.query(prompt))
            
            st.write("Gerando resposta...")
            # Gerar prompt completo
            full_prompt = f"""Você é um especialista em IHC (Interação Humano-Computador) com vasta experiência acadêmica e prática.
Sua tarefa é fornecer respostas precisas e bem fundamentadas, baseadas no contexto fornecido.
[DIRETRIZES]
- Use português brasileiro formal
- Mantenha termos técnicos consolidados em inglês
- Organize a resposta em parágrafos claros e concisos
- Mencione autores/fontes quando relevante
[CONTEXTO]
{context}
Pergunta: {prompt}
Forneça uma resposta direta e bem estruturada, desenvolvendo a explicação com detalhes relevantes e concluindo com aspectos práticos. Se houver diferentes visões na literatura, apresente-as.
"""
            # Gerar resposta
            response = generate_response_with_gemini(full_prompt)
            
            if response:
                response = response.replace('[PERGUNTA]', '').replace('[RESPOSTA]', '').strip()
                # Adicionar mensagem do assistente
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )
                
                # Exibir mensagem do assistente
                with st.chat_message("assistant"):
                    st.write(response)
                
                # Atualizar chat no Firebase
                if chat_id:
                    chat_data = {
                        "user_id": st.session_state.user_id,
                        "title": st.session_state.chats[chat_id]["title"],
                        "created_at": st.session_state.chats[chat_id]["created_at"],
                        "updated_at": get_brasilia_time(),
                        "messages": st.session_state.messages
                    }
                    save_chat_to_firebase(chat_id, chat_data)
            
            status.update(label="Resposta gerada!", state="complete", expanded=False)

# Fluxo principal do aplicativo
def main():
    try:
        # Verificar se o usuário está logado
        if "user_id" not in st.session_state or not st.session_state.user_id:
            show_auth_page()
        else:
            # Layout principal: barra lateral + chat
            handle_chats()
            show_chat_interface()
    except Exception as e:
        st.error(f"Erro durante a execução: {str(e)}")

if __name__ == "__main__":
    main()
