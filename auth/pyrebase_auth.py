import pyrebase
import streamlit as st

@st.cache_resource(show_spinner=False)
def initialize_pyrebase():
    try:
        firebase_config = {
            "apiKey": st.secrets["FIREBASE_API_KEY"],
            "authDomain": st.secrets["FIREBASE_AUTH_DOMAIN"],
            "databaseURL": st.secrets["FIREBASE_DATABASE_URL"],
            "projectId": st.secrets["FIREBASE_PROJECT_ID"],
            "storageBucket": st.secrets["FIREBASE_STORAGE_BUCKET"],
            "messagingSenderId": st.secrets["FIREBASE_MESSAGING_SENDER_ID"],
            "appId": st.secrets["FIREBASE_APP_ID"]
        }
        firebase = pyrebase.initialize_app(firebase_config)
        return firebase
    except Exception as e:
        st.error(f"Erro ao inicializar Pyrebase: {str(e)}")
        return None
