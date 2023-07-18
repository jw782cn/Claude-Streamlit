import streamlit as st
from chatbots.claude import Claude, models, ASK_TEMPLATE
import time
from config import *
import json

# Configures
st.set_page_config(layout="wide")
st.title("💬 Claude API Version")

# Sidebar
st.sidebar.title("Settings")

# api_key = st.sidebar.text_input("ANTHROPIC API Key", type="password", value=anthropic_api_key)
model = st.sidebar.selectbox("Model", models)
temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.1, 0.1)
system_prompt = st.sidebar.text_area("System Prompt", value=ASK_TEMPLATE)
stream = st.sidebar.checkbox("Stream", value=True)

# Main
# button: creat bot
# after click button, initial
def initialization():
    """
    Initialize the bot.
    """
    st.session_state.bot = Claude(model=model, temperature=temperature, system_prompt=system_prompt, stream=stream)
    if "messages" not in st.session_state:
        st.session_state.messages = []
create_bot = st.sidebar.button("Create Bot", on_click=initialization)

# Function to clear the messages and bot object
def clear_session():
    """
    Clear the session.
    """
    st.session_state["messages"] = []
    st.session_state["bot"] = None
# Button: Clear
clear_button = st.sidebar.button("Clear", on_click=clear_session)

# Button: save history messages
def save_history():
    """
    Save the history messages and provide a download link.
    """
    if not st.session_state.messages:
        st.info("No Messages", icon="ℹ️")
        st.stop()

    # Generate save title
    save_title = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    messages_json = json.dumps(st.session_state["messages"])

    # Save the JSON string to a file
    filename = f"messages_{save_title}.json"
    with open(filename, "w") as file:
        file.write(messages_json)
    
    # Provide download link
    file_link = f"[Download History](./{filename})"
    st.markdown(file_link, unsafe_allow_html=True)
# button
download_button = st.sidebar.button("Download History", on_click=save_history)

if "bot" not in st.session_state:
    initialization()
if "messages" not in st.session_state:
    st.session_state.messages = []

if st.session_state.get("bot") is None:
    """
    Please create the bot first.
    """

"""
Welcome to claude api version!
"""


for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="🧑‍💻" if message["role"]=="user" else "🤖"):
        st.markdown(message["content"])

disable_input = st.session_state.bot is None

if prompt := st.chat_input("", key="input", disabled=disable_input):
    if not st.session_state.bot:
        st.info("Please create bot first!")
        st.stop()
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        full_response = ""
        for response in st.session_state.bot.ask_llm(prompt,stream=True):
            full_response += response
            message_placeholder.write(full_response + "▌")
        message_placeholder.write(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})