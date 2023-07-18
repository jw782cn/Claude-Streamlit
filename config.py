import promptlayer
import streamlit as st
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

# env
# pinecone_api_key = st.secrets["PINECONE_API_KEY"]
# pinecone_env = st.secrets["PINECONE_ENV"]
# pinecone.init(api_key=pinecone_api_key, environment=pinecone_env,)
# index = pinecone.Index("openai")

# openai
promptlayer.api_key = st.secrets.get("PROMPTLAYER_API_KEY", "")
openai = promptlayer.openai
openai_api_key = st.secrets.get("OPENAI_API_KEY", "")
api_base = st.secrets.get("OPENAI_API_BASE", "")
openai.api_key = openai_api_key
if api_base != "":
    openai.api_base = api_base

# anthropic
anthropic_api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
anthropic = Anthropic(api_key=anthropic_api_key)
# anthropic = promptlayer.anthropic
# client = anthropic.Client(api_key=anthropic_api_key)
