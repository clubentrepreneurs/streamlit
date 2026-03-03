import streamlit as st
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Qdrant
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import qdrant_client
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="UniBot RAG 2026", layout="wide")

# Récupération sécurisée des clés
try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    Q_URL = st.secrets["QDRANT_URL"]
    Q_KEY = st.secrets["QDRANT_API_KEY"]
except Exception as e:
    st.error(f"Erreur de configuration des Secrets : {e}")
    st.stop()

# Initialisation des modèles (Version 004 pour l'embedding)
try:
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=GEMINI_KEY)
    embeddings = GoogleGenerativeAIEmbeddings(model="embedding-001", google_api_key=GEMINI_KEY)
except Exception as e:
    st.error(f"Erreur d'initialisation des modèles Google : {e}")
    st.stop()

# Connexion Qdrant
client = qdrant_client.QdrantClient(url=Q_URL, api_key=Q_KEY)
COLLECTION_NAME = "universite_savoir"

# --- 2. ADMINISTRATION (INDEXATION) ---
with st.sidebar:
    st.title("⚙️ Administration")
    uploaded_files = st.file_uploader("Uploader vos PDF de cours", type="pdf", accept_multiple_files=True)
    
    if uploaded_files and st.button("🚀 Indexer les documents"):
        with st.spinner("Transformation des PDF en vecteurs..."):
            all_docs = []
            for uploaded_file in uploaded_files:
                temp_path = f"temp_{uploaded_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                loader = PyPDFLoader(temp_path)
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
                docs = loader.load_and_split(text_splitter)
                all_docs.extend(docs)
                os.remove(temp_path)
            
            # Stockage dans Qdrant
            Qdrant.from_documents(
                all_docs, 
                embeddings, 
                url=Q_URL, 
                api_key=Q_KEY, 
                collection_name=COLLECTION_NAME,
                force_recreate=True # On recrée la collection pour éviter les conflits d'embeddings
            )
            st.success("Base de connaissances mise à jour !")

# --- 3. INTERFACE DE CHAT ---
st.title("🎓 Assistant Étudiant Intelligent")

# Vérification si la collection existe
try:
    vectorstore = Qdrant(client=client, collection_name=COLLECTION_NAME, embeddings=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # Chaîne RAG moderne
    template = """Tu es un assistant universitaire. Réponds à la question en utilisant le contexte fourni. 
    Si la réponse n'est pas dans le contexte, dis-le.
    
    CONTEXTE : {context}
    QUESTION : {question}
    RÉPONSE :"""
    
    prompt_template = ChatPromptTemplate.from_template(template)
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt_template
        | llm
        | StrOutputParser()
    )

    # Gestion des messages
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Posez votre question sur les cours..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                response = rag_chain.invoke(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Erreur lors de la génération : {e}")

except Exception:
    st.info("👋 Bienvenue ! Veuillez d'abord indexer des documents dans la barre latérale pour commencer.")
