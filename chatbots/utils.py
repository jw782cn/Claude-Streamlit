import tiktoken
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Callable, cast
from termcolor import colored
import requests
import json
from config import *


def tiktoken_gpt3_len(text: str) -> int:
    return len(tiktoken_gpt3_fn(text))


def tiktoken_gpt3_fn(text: str) -> List[str]:
    '''
    https://platform.openai.com/docs/models/gpt-3-5
    '''
    if text == "":
        return []
    enc = tiktoken.get_encoding("cl100k_base")
    _tokenizer = cast(Callable[[str], List], enc.encode)
    return _tokenizer(text, disallowed_special=())


# https://platform.openai.com/tokenizer ,gpt3.5每个字占用的token数更少
tokenizer = tiktoken.get_encoding('gpt2')


# create the length function
def tiktoken_len(text: str) -> int:
    tokens = tokenizer.encode(
        text,
        disallowed_special=()
    )
    return len(tokens)


def load_documents(text_path):
    loader = PyPDFLoader(text_path)
    return loader.load()


def split_chunks(sources, chunk_size=512, chunk_overlap=32):
    chunks = []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    for chunk in splitter.split_documents(sources):
        chunks.append(chunk)
    return chunks


def embedding(text):
    EMBEDDING_MODEL = "text-embedding-ada-002"
    res = openai.Embedding.create(
        input=[text], engine=EMBEDDING_MODEL
    )
    return res['data'][0]["embedding"]


def get_embeddings(chunks):
    EMBEDDING_MODEL = "text-embedding-ada-002"
    res = openai.Embedding.create(
        input=[c.page_content for c in chunks], engine=EMBEDDING_MODEL
    )
    # extract embeddings to a list
    embeds = [record['embedding'] for record in res['data']]
    return embeds


def get_chunks(chunks, embeddings, file_name):
    results = []
    for i in range(len(chunks)):
        results.append({
            'id': "vec-" + file_name + "-" + str(i),
            'values': embeddings[i],
            'metadata': {'context': chunks[i].page_content, 'page': chunks[i].metadata['page'], 'source': file_name}
        })
    return results


def read_pdf_from_local_path_then_chunk_embedding(local_path, file_name, index):
    result = load_documents(local_path)
    chunks = split_chunks(result)
    embeds = get_embeddings(chunks)
    results = get_chunks(chunks, embeds, file_name)
    # split into batches with size 100
    for i in range(0, len(results), 100):
        # if last batch is less than 100
        if i+100 > len(results):
            index.upsert(vectors=results[i:])
            break
        index.upsert(vectors=results[i:i+100])
    # index.upsert(vectors=results)


def query(index, question, top_k=3):
    embeds = embedding(question)
    # print(embeds)
    result = index.query(
        vector=embeds,
        top_k=top_k,
        # include_values=True,
        include_metadata=True
    )
    return result


def assemble_text(result, limit=3000):
    text = ""
    result = result["matches"]
    for r in result:
        current = "===\n"
        source = r.metadata['source'].split("/")[-1]
        page = int(r.metadata['page'])
        current += f"source: {source} page: {page} score: {r.score}\n"
        current += "context:\n"
        current += r.metadata['context']
        current += "\n===\n"
        if tiktoken_gpt3_len(current) + tiktoken_gpt3_len(text) < limit:
            text += current
        else:
            break
    return text


def get_knowledge_from_document(index, question, top_k=30, limit=3000):
    result = query(index, question, top_k)
    text = assemble_text(result, limit)
    return text


def chat_completion_request(messages, type="GPT", model="gpt-3.5-turbo", stream=False, temperature=0.1, tags=[], max_tokens=10000):
    if type == "GPT":
        return openai.ChatCompletion.create(
            model=model,
            messages=messages,
            stream=stream,
            temperature=temperature,
            pl_tags=tags
        )
    else:
        # assemble messages into one prompt
        
        prompt = ""
        for m in messages:
            if m["role"] == "user" or m["role"] == "system":
                prompt += f"{HUMAN_PROMPT} {m['content']}"
            else:
                prompt += f"{AI_PROMPT} {m['content']}"
        prompt += f"{AI_PROMPT}"
        return anthropic.completions.create(
                model=model,
                prompt=prompt,
                temperature=temperature,
                max_tokens_to_sample=max_tokens,
                stream=stream,
            )


def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301"):
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model in {
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
    }:
        tokens_per_message = 3
        tokens_per_name = 1
    elif model == "gpt-3.5-turbo-0301":
        # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_message = 4
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif "gpt-3.5-turbo" in model:
        print("Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
    elif "gpt-4" in model:
        print(
            "Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
        return num_tokens_from_messages(messages, model="gpt-4-0613")
    else:
        return 0
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


def pretty_print_conversation(messages):
    role_to_color = {
        "system": "red",
        "user": "green",
        "assistant": "blue",
        "function": "magenta",
    }
    formatted_messages = []
    for message in messages:
        if message["role"] == "system":
            formatted_messages.append(f"system: {message['content']}\n")
        elif message["role"] == "user":
            formatted_messages.append(f"user: {message['content']}\n")
        elif message["role"] == "assistant" and message.get("function_call"):
            formatted_messages.append(
                f"assistant: {message['function_call']}\n")
        elif message["role"] == "assistant" and not message.get("function_call"):
            formatted_messages.append(f"assistant: {message['content']}\n")
        elif message["role"] == "function":
            formatted_messages.append(
                f"function ({message['name']}): {message['content']}\n")
    for formatted_message in formatted_messages:
        print(
            colored(
                formatted_message,
                role_to_color[messages[formatted_messages.index(
                    formatted_message)]["role"]],
            )
        )
