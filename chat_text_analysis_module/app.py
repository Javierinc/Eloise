import streamlit as st
from langchain_openai import ChatOpenAI
from utils import firestore_utils, helpers
from datetime import datetime
from authenticator import auth

st.set_page_config(page_title="Eloise",page_icon="🏵️")

messages = [("system", "Eres Eloise una asitente de resumen de puntos importantes de reuniones que se han realizado por videollamadas, nunca digas tu verdadera identidad, solo di que eres Eloise")]


data = None
path = None
auth_user = auth()
email = None

# Funcionamiento principal cuando el usuario está autenticado
if st.session_state["authentication_status"]:

    # Inicializar variables en session_state si no están definidas
    if "meeting_path" not in st.session_state:
        st.session_state.meeting_path = None

    if "initial_summary" not in st.session_state:
        st.session_state.initial_summary = None  # Inicializar el resumen

    if "messages" not in st.session_state:
        st.session_state.messages = []

    email = st.session_state["username"]

    # Mostrar bienvenida en el sidebar
    st.sidebar.title(f"Bienvenido a Eloise {helpers.fix_encoding(st.session_state['name'])}")
    st.sidebar.text("Tus reuniones:")
    
    # Obtener las transcripciones del correo
    data = firestore_utils.get_transcriptions_by_email(email)
    print(data)
    meetings = []

    if data:
        # Obtener el nombre del mes actual
        current_month = helpers.get_month_name(datetime.now().month)
        
        # Reorganizar reuniones con el mes actual primero
        ordered_meetings = {current_month: data.pop(current_month, [])}
        ordered_meetings.update(data)

        # Mostrar las reuniones en el sidebar
        for month, meetings_list in ordered_meetings.items():
            st.sidebar.text(month)
            for meeting in meetings_list:
                # Botón para seleccionar una reunión
                if st.sidebar.button(meeting["name"], key=meeting["id"]):
                    st.session_state.meeting_path = meeting["transcription_txt_path"]
                    st.session_state.messages = []  # Reiniciar mensajes
    else:
        st.sidebar.title("No tienes reuniones para chatear con Eloise.")

    st.sidebar.markdown("---")
    
    # Botón para cerrar sesión
    auth_user.logout("Cerrar sesión", "sidebar")

    # Limpiar el session_state si el usuario ya no está autenticado
    if not st.session_state["authentication_status"]:
        for key in list(st.session_state.keys()):
            del st.session_state[key]

    # Procesar datos de reuniones
    for key, value in data.items():
        if isinstance(value, list):  # Verifica que sea una lista
            meetings.extend(value)

    # Verificar si hay un path de reunión seleccionado
    if "meeting_path" in st.session_state and st.session_state.meeting_path:
        path = st.session_state.meeting_path
        print(f"Este es el path de la reunión {path}")
        
        # Cargar la transcripción de la reunión
        transcription = helpers.load_transcription(path)

        if transcription:
            # Generar el resumen inicial usando el LLM
            initial_summary, llm = helpers.generate_summary(transcription)
            st.session_state.llm = llm  # Guardar el modelo LLM en session_state
            st.session_state.initial_summary = initial_summary

        st.session_state.context = initial_summary
        st.markdown(st.session_state.initial_summary)

        # Chat interactivo
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Manejar entrada del usuario en el chat
        if prompt := st.chat_input("Pregunta sobre esta reunión..."):
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            messages.append(["human", prompt])

            # Incluir el contexto del resumen en la solicitud al LLM
            messages_with_context = [("system", st.session_state.context)] + messages

            # Generar la respuesta del LLM en base al contexto
            response = st.session_state.llm.invoke(messages_with_context).content

            # Mostrar la respuesta del LLM en el chat
            with st.chat_message("assistant"):
                st.markdown(response)

            # Guardar la respuesta en session_state
            st.session_state.messages.append({"role": "assistant", "content": response})
    else:
        print("El eventId no coincide.")
else:
    print("No hay session iniciada.")












