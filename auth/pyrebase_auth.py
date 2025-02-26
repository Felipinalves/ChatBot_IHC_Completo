import pyrebase
import streamlit as st

@st.cache_resource(show_spinner=False)
def initialize_pyrebase():
    try:
        firebase_config = {
            "apiKey": st.secrets["FIREBASE"]["apiKey"],
            "authDomain": st.secrets["FIREBASE"]["authDomain"],
            "projectId": st.secrets["FIREBASE"]["projectId"],
            "storageBucket": st.secrets["FIREBASE"]["storageBucket"],
            "messagingSenderId": st.secrets["FIREBASE"]["messagingSenderId"],
            "appId": st.secrets["FIREBASE"]["appId"],
            "databaseURL": ""
        }
        firebase = pyrebase.initialize_app(firebase_config)
        return firebase
    except Exception as e:
        st.error(f"Erro ao inicializar Pyrebase: {str(e)}")
        return None
