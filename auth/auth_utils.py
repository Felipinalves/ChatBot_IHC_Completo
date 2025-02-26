import json
import streamlit as st

def login_with_email(auth, email, password):
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

def register_user(auth, db, email, password, name):
    try:
        user = auth.create_user_with_email_and_password(email, password)
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
