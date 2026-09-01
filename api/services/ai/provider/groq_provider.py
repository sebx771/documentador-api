import logging
from groq import Groq
from .base_provider import BaseAIProvider
from .structures import ChatCompletionResponse, ChatCompletionChoice, ChatCompletionMessage
from ....config import config

logger = logging.getLogger(__name__)


class GroqProvider(BaseAIProvider):
    def _get_env_api_key(self) -> str | None:
        groq_api_key= config.GROQ_API_KEY
        return groq_api_key

    def _initialize_client(self) -> Groq:
        client = Groq(api_key=self.api_key)
        logger.info("Cliente Groq inicializado correctamente")
        return client

    def create_chat_completion(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> ChatCompletionResponse:
        completion = self.client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return ChatCompletionResponse(
            choices=[
                ChatCompletionChoice(
                    message=ChatCompletionMessage(
                        content=completion.choices[0].message.content
                    )
                )
            ]
        )
