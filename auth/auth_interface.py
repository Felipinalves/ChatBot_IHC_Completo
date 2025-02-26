import streamlit as st
from auth.auth_utils import login_with_email, register_user, reset_password
from utils.time_utils import get_brasilia_time

def show_auth_page(auth, db):
    """Exibe a página de autenticação (login, cadastro, recuperação de senha)"""
    
    if "auth_page" not in st.session_state:
        st.session_state.auth_page = "login"  # login, register, reset
    
    if "email" not in st.session_state:
        st.session_state.email = ""
        
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("IAHC Chatbot 🤖")
        
        # Tabs para diferentes opções de autenticação
        tab = st.tabs(["Login", "Cadastro", "Recuperar Senha"])
        
        with tab[1]:
            st.subheader("Login")
            
            email = st.text_input("E-mail", key="login_email")
            password = st.text_input("Senha", type="password", key="login_password")
            
            col_login_btn, col_google_btn = st.columns(2)
            
            with col_login_btn:
                if st.button("Entrar", use_container_width=True):
                    if email and password:
                        user, error = login_with_email(auth, email, password)
                        if user:
                            st.session_state.user_id = user['localId']
                            st.session_state.id_token = user['idToken']
                            st.session_state.refresh_token = user['refreshToken']
                            st.session_state.email = user['email']
                            
                            # Obter informações do usuário
                            user_info = db.child("users").child(user['localId']).get().val()
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
                    st.info("Redirecionando para autenticação Google...")
                    # Implementar redirecionamento para autenticação Google
        
        with tab[2]:
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
                        user, error = register_user(auth, db, email, password, name)
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
        
        with tab[3]:
            st.subheader("Recuperar senha")
            
            email = st.text_input("Digite seu e-mail", key="reset_email")
            
            if st.button("Enviar link de recuperação", use_container_width=True):
                if email:
                    success, message = reset_password(auth, email)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.warning("Por favor, digite seu e-mail.")
