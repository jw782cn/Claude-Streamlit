"""
Module Name: chatgpt.py
Description: This module contains the implementation of a chatbot using Claude's models.
Author: Chenran
"""
import time
from chatbots.utils import (
    num_tokens_from_messages,
    read_pdf_from_local_path_then_chunk_embedding,
    chat_completion_request,
)

models = ["claude-2.0", "claude-1", "claude-v1-100k"]

context_windows = {
    "claude-2.0": 100000,
    "claude-1":100000,
}

CLAUDE_MODEL = "claude-2.0"

ASK_TEMPLATE = """
You are a helpful assistant developed by Claude.
"""


class Claude:
    """A chatbot powered by OpenAI's GPT models."""

    def __init__(self, model=CLAUDE_MODEL, temperature=0.1,
                 index=None, file_name=None, system_prompt=None, stream=False):
        """
        Initialize the ChatBot.

        Args:
            model (str): The GPT model to use. Defaults to GPT_MODEL.
            temperature (float): The temperature for text generation. Defaults to 0.1.
            index: Optional index argument.
            file_name (str): Optional file name.
            system_prompt (str): Optional system prompt.
        """
        self.model = model
        self.messages = []
        self.temperature = temperature
        self.index = index
        self.file_name = file_name
        self.stream = stream
        if system_prompt:
            self.system_prompt = system_prompt
        else:
            self.system_prompt = ASK_TEMPLATE

    def change_settings(self, **args):
        """
        Change the settings of the ChatBot.

        Args:
            **args: Keyword arguments representing the settings to be changed.
        """
        # change args
        for key, value in args.items():
            setattr(self, key, value)

    def set_file(self, file_name):
        """
        Set the file name.

        Args:
            file_name (str): The name of the file.
        """
        self.file_name = file_name

    def upload_file(self, file_path, file_name):
        """
        Upload a file and perform chunk embedding.

        Args:
            file_path (str): The path to the file.
            file_name (str): The name of the file.
        """
        read_pdf_from_local_path_then_chunk_embedding(
            file_path, file_name, self.index)

    def assemble_history_messages(self, system_message, question_message):
        """
        Assemble history messages.

        Args:
            system_message (Any): The system message.
            question_message (Any): The question message.

        Returns:
            list: A list of assembled history messages.
        """
        # don't exceed limit
        limit = context_windows[self.model]
        tokens = num_tokens_from_messages(
            [system_message, question_message])
        messages = [question_message]
        # reversed to get the latest messages
        for message in reversed(self.messages):
            message = {"role": message["role"], "content": message["content"]}
            tokens += num_tokens_from_messages([message])
            if tokens > limit:
                break
            messages.append(message)
        messages.append(system_message)
        return list(reversed(messages))

    def add_message(self, question_message, assistant_message):
        """
        Add a question and assistant message to the chat history.

        Args:
            question_message (Any): The question message.
            assistant_message (Any): The assistant message.
        """
        self.messages.append(question_message)
        self.messages.append(assistant_message)

    def ask_llm(self, question, stream=False):
        """
        Ask a question to the chatbot.

        Args:
            question (str): The question to ask.
            stream (bool): Whether to stream the response. Defaults to False.

        Yields:
            str: The generated response.
        """
        start_time = time.time()
        system_message = {"role": "system", "content": self.system_prompt}
        question_message = {"role": "user", "content": question}
        # limit
        messages = self.assemble_history_messages(
            system_message, question_message)
        chat_response = chat_completion_request(
            messages, type="claude", model=self.model, temperature=self.temperature, tags=["claude", self.model], stream=stream
        )
        # stream
        if stream:
            full_answer = ""
            for chunk in chat_response:
                # print(chunk)
                assistant_message = chunk.completion
                # content
                if assistant_message:
                    full_answer += assistant_message
                    yield assistant_message
            self.add_message(question_message, {
                             "role": "assistant", "content": full_answer})
            end_time = time.time()
            print("Answer Time:", end_time - start_time, "seconds")
            return

        # not stream
        assistant_message = chat_response.get("completion")
        if assistant_message:
            # answer directly
            answer = assistant_message
            self.add_message(question_message, {
                             "role": "assistant", "content": answer})
            end_time = time.time()
            print("Answer Time:", end_time - start_time, "seconds")
            yield answer
