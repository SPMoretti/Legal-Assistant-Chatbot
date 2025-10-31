import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv
from load import save_uploaded_file, list_uploaded_files
from rag import RAGChatbot
from prompt_base import SYSTEM_PROMPT

load_dotenv()

st.set_page_config(page_title="Asistente Legal IA", page_icon="⚖️", layout="wide")

# --- Diccionario de traducciones ---
TRANSLATIONS = {
    "es": {
        "title": "⚖️ Asistente Legal Inteligente",
        "documents": "📂 Documentos",
        "upload": "Subí un PDF o DOCX",
        "refresh_files": "Refrescar lista de archivos",
        "select_doc": "🗂️ Selección de documento",
        "load_doc": "Cargar archivo en memoria del LLM",
        "tokens": "🔢 Tokens usados",
        "chat": "💬 Chat con el asistente legal",
        "input_placeholder": "Escribí tu mensaje...",
        "first_load_warning": "Primero cargá y procesá un documento.",
        "chatbot_error": "El chatbot no está inicializado."
    },
    "en": {
        "title": "⚖️ Legal AI Assistant",
        "documents": "📂 Documents",
        "upload": "Upload a PDF or DOCX",
        "refresh_files": "Refresh file list",
        "select_doc": "🗂️ Document selection",
        "load_doc": "Load document into LLM memory",
        "tokens": "🔢 Tokens used",
        "chat": "💬 Chat with the legal assistant",
        "input_placeholder": "Type your message...",
        "first_load_warning": "Please load and process a document first.",
        "chatbot_error": "The chatbot is not initialized."
    }
}

# --- Selección de idioma ---
if "language" not in st.session_state:
    st.session_state.language = "es"

with st.sidebar:
    lang = st.selectbox("Idioma / Language", options=["Español", "English"])
    st.session_state.language = "es" if lang == "Español" else "en"

t = TRANSLATIONS[st.session_state.language]

# --- Título ---
st.title(t["title"])

# --- Inicializar chatbot ---
if "chatbot" not in st.session_state:
    try:
        st.session_state.chatbot = RAGChatbot(system_prompt=SYSTEM_PROMPT)
    except Exception as e:
        st.error(f"Error al inicializar el chatbot: {e}")

# --- Refrescar archivos usando session_state ---
if "refresh_flag" not in st.session_state:
    st.session_state.refresh_flag = False

# --- Barra lateral simplificada ---
with st.sidebar:
    st.header(t["documents"])
    uploaded_file = st.file_uploader(t["upload"], type=["pdf", "docx"])
    if uploaded_file is not None:
        try:
            filepath = save_uploaded_file(uploaded_file)
            st.success(f"{os.path.basename(filepath)} saved successfully")
        except Exception as e:
            st.error(f"Could not save file: {e}")

    if st.button(t["refresh_files"]):
        st.session_state.refresh_flag = not st.session_state.refresh_flag

    st.markdown("---")
    st.subheader(t["select_doc"])
    files = list_uploaded_files()
    if files:
        selected_file = st.selectbox("Select file:", files)
        if st.button(t["load_doc"]):
            if selected_file:
                try:
                    file_path = os.path.join("archivos", selected_file)
                    st.session_state.chatbot.load_document(file_path)
                    st.success(f"{selected_file} loaded successfully.")
                except Exception as e:
                    st.error(f"Error loading document: {e}")
            else:
                st.warning("Select a file first.")
    else:
        st.info("No files found. Upload one above.")

    st.markdown("---")
    st.subheader(t["tokens"])
    st.write(st.session_state.get("tokens_used", 0))

# --- Chat interactivo ---
st.subheader(t["chat"])

if "messages" not in st.session_state:
    st.session_state.messages = []

chat_container = st.container()

if st.session_state.get("chatbot") is None:
    st.warning(t["chatbot_error"])
else:
    user_input = st.chat_input(t["input_placeholder"])
    if user_input:
        if st.session_state.chatbot.collection is None:
            st.warning(t["first_load_warning"])
        else:
            with st.spinner("Generating response..."):
                try:
                    # Instrucción de idioma para LLM
                    language_instruction = ""
                    if st.session_state.language == "en":
                        language_instruction = "Please answer in English."
                    else:
                        language_instruction = "Por favor responde en Español."

                    response, tokens = st.session_state.chatbot.ask(
                        user_input,
                        language_instruction=language_instruction
                    )
                    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
                    st.session_state.messages.append(("Usuario", user_input, timestamp))
                    st.session_state.messages.append(("Asistente", response, timestamp))
                    st.session_state.tokens_used = tokens
                except Exception as e:
                    st.error(f"Error generating response: {e}")

# --- Mostrar historial estilo WhatsApp con timestamp ---
with chat_container:
    for role, message, timestamp in st.session_state.messages:
        if role == "Usuario":
            st.markdown(
                f"""
                <div style="display:flex; justify-content:flex-end; margin:5px;">
                    <div style="background-color:#E5E5EA; color:black; padding:10px; border-radius:15px; max-width:70%;">
                        {message}<br>
                        <span style="font-size:10px; color:#555;">{timestamp}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div style="display:flex; justify-content:flex-start; margin:5px;">
                    <div style="background-color:#0B93F6; color:white; padding:10px; border-radius:15px; max-width:70%;">
                        {message}<br>
                        <span style="font-size:10px; color:#EEE;">{timestamp}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True
            )

# --- Scroll automático al final ---
st.markdown(
    """
    <script>
        const chatContainer = window.parent.document.querySelector('main');
        if(chatContainer){ chatContainer.scrollTop = chatContainer.scrollHeight; }
    </script>
    """,
    unsafe_allow_html=True
)










