import streamlit as st
from auth.auth_utils import login_with_email, register_user, reset_password
from utils.time_utils import get_brasilia_time

def show_auth_page(auth, firestore_db):
    """Mostra a página de autenticação"""
    st.title("🤖 Bem-vindo ao IAHC ChatBot!")
    
    tab = st.tabs(["Login", "Cadastro", "Recuperar Senha"])
    
    with tab[0]:
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
    
    with tab[1]:
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
    
    with tab[2]:
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
