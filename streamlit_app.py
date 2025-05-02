# import streamlit as st
# import requests
# import os
# import json

# # Constants
# API_URL = "http://localhost:8000/chat"
# CHAT_DIR = "chat_logs"
# os.makedirs(CHAT_DIR, exist_ok=True)

# # Streamlit page setup
# st.set_page_config(page_title="Mental Health Chatbot", page_icon="💬")
# st.title("🧠 Mental Health Assistant Chatbot")

# # User ID input
# username = st.text_input("Enter your username to continue:", key="username")

# # Exit early if no username
# if not username:
#     st.warning("Please enter your username to start chatting.")
#     st.stop()

# # Chat file path
# chat_file = os.path.join(CHAT_DIR, f"{username}.json")

# # Load existing chat history
# if os.path.exists(chat_file):
#     with open(chat_file, "r") as f:
#         st.session_state.messages = json.load(f)
# else:
#     st.session_state.messages = []

# # Sidebar for clearing chat
# with st.sidebar:
#     if st.button("🗑️ Clear Chat History"):
#         st.session_state.messages = []
#         if os.path.exists(chat_file):
#             os.remove(chat_file)
#         st.experimental_rerun()

# # Display previous chat
# for msg in st.session_state.messages:
#     with st.chat_message(msg["role"]):
#         st.markdown(msg["content"])

# # Chat input
# prompt = st.text_input("Type your message here...")

# # On message send
# if prompt:
#     # Add user message
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     with st.chat_message("user"):
#         st.markdown(prompt)

#     # Send to backend
#     with st.chat_message("assistant"):
#         with st.spinner("Thinking..."):
#             try:
#                 response = requests.post(API_URL, json={"question": prompt, "top_k": 3})
#                 if response.status_code == 200:
#                     data = response.json()
#                     ai_reply = data.get("answer", "I couldn't find an answer.")
#                 else:
#                     ai_reply = "❌ Backend error."
#             except Exception as e:
#                 ai_reply = f"⚠️ Error: {e}"

#             st.markdown(ai_reply)
#             st.session_state.messages.append({"role": "assistant", "content": ai_reply})

#     # Save chat to file
#     with open(chat_file, "w") as f:
#         json.dump(st.session_state.messages, f, indent=2)



import streamlit as st
import sqlite3
import requests
from datetime import datetime

API_URL = "http://localhost:8000/chat"  # Your FastAPI endpoint

# Function to connect to SQLite
def get_db():
    return sqlite3.connect("chat_history.db", detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

# Save message
def save_message(username, role, message):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO chat_history (username, role, message, timestamp) VALUES (?, ?, ?, ?)",
              (username, role, message, datetime.now()))
    conn.commit()
    conn.close()

# Get chat history
def get_user_history(username):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT role, message, timestamp FROM chat_history WHERE username = ? ORDER BY timestamp", (username,))
    data = c.fetchall()
    conn.close()
    return data

# Streamlit UI
st.set_page_config("🧠 Mental Health Chatbot", page_icon="💬")
st.title("🧠 Mental Health Assistant (Streamlit + FastAPI + SQLite)")

# Login
username = st.text_input("Enter your username to begin:", key="user_input")
if not username:
    st.warning("Please enter a username to start.")
    st.stop()

st.success(f"Logged in as: {username}")

# Chat history
st.markdown("## 🕘 Previous Messages")
for role, msg, ts in get_user_history(username):
    with st.chat_message(role):
        st.markdown(f"**[{ts}]** {msg}")

# Chat input
prompt = st.chat_input("Ask something...")

if prompt:
    # Save user message
    st.chat_message("user").markdown(prompt)
    save_message(username, "user", prompt)

    # Send to FastAPI
    try:
        response = requests.post(API_URL, json={"question": prompt, "top_k": 3})
        if response.status_code == 200:
            answer = response.json().get("answer", "No answer found.")
        else:
            answer = "Backend error!"
    except Exception as e:
        answer = f"Error contacting FastAPI: {e}"

    # Show and save response
    st.chat_message("assistant").markdown(answer)
    save_message(username, "assistant", answer)
