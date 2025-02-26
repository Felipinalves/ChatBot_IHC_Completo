import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import json

def get_firebase_credentials():
    if "FIREBASE_SERVICE_ACCOUNT" in st.secrets:
        return json.loads(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
    elif "firebase" in st.secrets:
        firebase_config = st.secrets["firebase"]
        credentials_dict = {
            "type": firebase_config["type"],
            "project_id": firebase_config["project_id"],
            "private_key_id": firebase_config["private_key_id"],
            "private_key": firebase_config["private_key"],
            "client_email": firebase_config["client_email"],
            "client_id": firebase_config["client_id"],
            "auth_uri": firebase_config["auth_uri"],
            "token_uri": firebase_config["token_uri"],
            "auth_provider_x509_cert_url": firebase_config["auth_provider_x509_cert_url"],
            "client_x509_cert_url": firebase_config["client_x509_cert_url"],
            "universe_domain": firebase_config.get("universe_domain", "")
        }
        return credentials_dict
    else:
        raise Exception("Firebase credentials not found in Streamlit secrets.")

@st.cache_resource(show_spinner=False)
def initialize_firebase_admin():
    try:
        if not firebase_admin._apps:
            cred_dict = get_firebase_credentials()
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Erro ao inicializar Firebase Admin SDK: {str(e)}")
        return None
