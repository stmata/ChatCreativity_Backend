import os
import asyncio
from typing import List, Any, Iterator, AsyncIterator, Dict
from dotenv import load_dotenv
from openai import AzureOpenAI
from pydantic import PrivateAttr
from llama_index.core.llms.llm import LLM
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pydantic import BaseModel as PydanticBaseModel
from llama_index.core.memory.chat_summary_memory_buffer import ChatSummaryMemoryBuffer

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_VERSION = os.getenv("OPENAI_API_VERSION")
API_BASE = os.getenv("API_BASE")

if not API_KEY or not API_VERSION or not API_BASE:
    raise ValueError("Les variables d'environnement API_KEY, OPENAI_API_VERSION et API_BASE doivent être définies.")

try:
    client = AzureOpenAI(
        api_key=API_KEY,
        api_version=API_VERSION,
        azure_endpoint=API_BASE
    )
except Exception as e:
    raise RuntimeError(f"Erreur lors de l'initialisation du client Azure OpenAI : {e}")

class ChatResult(PydanticBaseModel):
    message: ChatMessage

class AzureOpenAIWrapper(LLM):
    _client: Any = PrivateAttr()
    
    def __init__(self, client, context_window: int = 4096):
        super().__init__()
        self._client = client
        self._metadata = type("Metadata", (), {"context_window": context_window})()

    @property
    def metadata(self):
        return self._metadata

    def chat(self, messages: List[ChatMessage], **kwargs) -> ChatResult:
        formatted_messages = [
            {"role": msg.role.value.lower(), "content": msg.content}
            for msg in messages
        ]
        response = self._client.chat.completions.create(
            model="gpt-4o",
            messages=formatted_messages,
            temperature=kwargs.get("temperature", 0.2),
            stream=False
        )
        content = ""
        for choice in response.choices:
            delta = choice.delta
            token = getattr(delta, "content", "")
            content += token
        result_message = ChatMessage(role=MessageRole.ASSISTANT, content=content)
        return ChatResult(message=result_message)

    def complete(self, prompt: str, **kwargs) -> ChatResult:
        messages = [ChatMessage(role=MessageRole.USER, content=prompt)]
        return self.chat(messages, **kwargs)

    def stream_chat(self, messages: List[ChatMessage], **kwargs) -> Iterator[str]:
        formatted_messages = [
            {"role": msg.role.value.lower(), "content": msg.content}
            for msg in messages
        ]
        response = self._client.chat.completions.create(
            model="gpt-4o",
            messages=formatted_messages,
            temperature=kwargs.get("temperature", 0.2),
            stream=True
        )
        for chunk in response:
            try:
                choices = chunk.choices
                if choices and len(choices) > 0:
                    delta = choices[0].delta
                    token = getattr(delta, "content", "")
                    if token:
                        yield token
            except Exception as e:
                continue

    def stream_complete(self, prompt: str, **kwargs) -> Iterator[str]:
        return self.stream_chat([ChatMessage(role=MessageRole.USER, content=prompt)], **kwargs)

    async def acomplete(self, prompt: str, **kwargs) -> ChatResult:
        return await asyncio.to_thread(self.complete, prompt, **kwargs)

    async def achat(self, messages: List[ChatMessage], **kwargs) -> ChatResult:
        return await asyncio.to_thread(self.chat, messages, **kwargs)

    async def astream_chat(self, messages: List[ChatMessage], **kwargs) -> AsyncIterator[str]:
        for token in self.stream_chat(messages, **kwargs):
            yield token

    async def astream_complete(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        async for token in self.astream_chat([ChatMessage(role=MessageRole.USER, content=prompt)], **kwargs):
            yield token

wrapped_client = AzureOpenAIWrapper(client, context_window=4096)

session_buffers: Dict[str, ChatSummaryMemoryBuffer] = {}

def get_buffer_for_session(session_id: str) -> ChatSummaryMemoryBuffer:
    if session_id not in session_buffers:
        session_buffers[session_id] = ChatSummaryMemoryBuffer.from_defaults(
            llm=wrapped_client,
            token_limit=128000,
            count_initial_tokens=False
        )
    return session_buffers[session_id]
