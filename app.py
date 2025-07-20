# --- app.py ---
import os
import streamlit as st
from dotenv import load_dotenv
from modules import auth, pdf_handler, vector_store
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from langchain.embeddings import OpenAIEmbeddings
import sqlite3
from datetime import datetime
import hashlib

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []


load_dotenv()

st.set_page_config(page_title="DocSage - Ask Your PDF", layout="wide")
st.title("📄 DocSage - Ask Your Document")

# Setup DB if it doesn't exist
conn = sqlite3.connect("chat_history.db")
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS chat (
    email TEXT,
    question TEXT,
    answer TEXT,
    timestamp TEXT
)''')
conn.commit()


# --- Authentication ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.email = None

if "show_email_input" not in st.session_state:
    st.session_state.show_email_input = False

if not st.session_state.authenticated:
    st.subheader("🔐 Login to Save Your Chats")

    if not st.session_state.show_email_input:
        if st.button("Login"):
            st.session_state.show_email_input = True
            st.rerun()
    else:
        email_input = st.text_input("Enter your email")
        if st.button("Submit") and email_input:
            st.session_state.authenticated = True
            st.session_state.email = email_input
            st.success(f"Welcome, {email_input}!")
            st.rerun()
else:
    st.markdown(f"✅ Logged in as `{st.session_state.email}`")
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.email = None
        st.session_state.show_email_input = False
        st.rerun()


# --- PDF Upload and Chunking ---
uploaded_files = st.file_uploader("📎 Upload one or more PDFs", type="pdf", accept_multiple_files=True)


if uploaded_files:
    for uploaded_file in uploaded_files:
        file_bytes = uploaded_file.read()
        file_hash = hashlib.md5(file_bytes).hexdigest()

        # Check if already processed
        if st.session_state.get("processed_files", {}).get(file_hash):
            st.success(f"✅ {uploaded_file.name} already processed!")
        else:
            with st.spinner(f"🔍 Processing {uploaded_file.name}..."):
                uploaded_file.seek(0)  # Reset pointer
                chunks = pdf_handler.process_pdf(uploaded_file)
                for chunk in chunks:
                    chunk["filename"] = uploaded_file.name  # ✅ Add filename to each chunk

                namespace = hashlib.md5(uploaded_file.name.encode()).hexdigest()
                vector_store.store_chunks_to_pinecone(chunks, uploaded_file.name, namespace=namespace)
                st.session_state.last_namespace = namespace  # Save it for querying

                # Log to database if authenticated
                if st.session_state.authenticated:
                    c.execute("INSERT INTO chat (email, question, answer, timestamp) VALUES (?, ?, ?, ?)",
                        (st.session_state.email, f"Processed {uploaded_file.name}", "Chunks stored", datetime.now().isoformat()))
                    conn.commit()           


                # Update session state
                if "processed_files" not in st.session_state:
                    st.session_state.processed_files = {}
                st.session_state.processed_files[file_hash] = True
                st.session_state.chunks_uploaded = True
                st.success(f"✅ {uploaded_file.name} is ready to chat with!")



# --- Chat Input at Top ---
if st.session_state.get("chunks_uploaded"):
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.subheader("💬 Ask a Question")
    query = st.text_input("Your question:", key="text_input_query")

    if query:
        with st.spinner("🤖 Thinking..."):
            # Embed question
            embedder = OpenAIEmbeddings()
            query_embedding = embedder.embed_query(query)

            # Pinecone lookup
            pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

            # Check/create index
            if 'my-index' not in pc.list_indexes().names():
                pc.create_index(
                    name='my-index',
                    dimension=1536,
                    metric='cosine',  # or 'euclidean' depending on your use
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'  # or your region
                    )
                )
            index = pc.Index("docsage-index")
            namespace = st.session_state.get("last_namespace", "default")
            results = index.query(vector=query_embedding, top_k=3, include_metadata=True, namespace=namespace)            # Group results by document name
           
            context_by_doc = {}
            for match in results["matches"]:
                doc_name = match["metadata"].get("filename", "Unknown Source")

                text = match["metadata"]["text"]
                context_by_doc.setdefault(doc_name, []).append(text)

            if st.session_state.authenticated:
                namespace = hashlib.md5((uploaded_file.name + st.session_state.email).encode()).hexdigest()
            else:
                namespace = hashlib.md5(uploaded_file.name.encode()).hexdigest()
    
            # Create merged context string
            context = "\n\n".join([
                f"From {doc_name}:\n" + "\n".join(texts)
                for doc_name, texts in context_by_doc.items()
            ])

            

                # Get response from OpenAI
            openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Answer the user's question using only the provided context. If multiple sources are used, indicate which file the info came from."},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
                ]
            )

            answer = response.choices[0].message.content

            st.chat_message("user").write(query)
            st.chat_message("assistant").markdown(f"**Answer:**\n{answer}")
            st.markdown("**Sources used:**")
            for source in context_by_doc:
                st.markdown(f"🔹 *{source}*")

            # Save history to session
            st.session_state.chat_history.append((query, answer))

            # Save to database if logged in
            if st.session_state.authenticated:
                c.execute("INSERT INTO chat (email, question, answer, timestamp) VALUES (?, ?, ?, ?)",
                    (st.session_state.email, query, answer, datetime.now().isoformat()))
                conn.commit()

# Display chat history
if st.session_state.chat_history:
    st.markdown("---")
    st.subheader("📜 Chat History")
        
    for q, a in reversed(st.session_state.chat_history):
        st.markdown(f"**You:** {q}")
        st.markdown(f"**DocSage:** {a}")
conn.close()
