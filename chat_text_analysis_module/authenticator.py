import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

#Carga las credenciales desde el archivo config.yaml
def auth():
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

    fields = {
    "Form name": "Eloise 🏵️\n Inicio de sesión",  # Título del formulario
    "Username": "Correo",            # Etiqueta para el campo de usuario
    "Password": "Contraseña",        # Etiqueta para el campo de contraseña
    "Login": "Iniciar sesión",        # Texto del botón de login
}
    
    authenticator.login(fields=fields)

    if st.session_state["authentication_status"]:
        return authenticator
    elif st.session_state["authentication_status"] is False:
        st.error("Usuario o Contraseña invalido")
    elif st.session_state["authentication_status"] is None:
        st.warning("Por favor, ingrese Usuario y Constraseña")



