# api/services/ai/providers/structures.py
from dataclasses import dataclass

@dataclass
class ChatCompletionMessage:
    content: str

@dataclass
class ChatCompletionChoice:
    message: ChatCompletionMessage

@dataclass
class ChatCompletionResponse:
    choices: list[ChatCompletionChoice]