from openai import OpenAI
from api.config import config
from .base_provider import BaseAIProvider
from .structures import ChatCompletionResponse, ChatCompletionChoice, ChatCompletionMessage

class OpenRouterProvider(BaseAIProvider):
    """
    Implementación del proveedor OpenRouter utilizando el SDK de OpenAI.
    Permite el uso de modelos gratuitos con amplia ventana de contexto para consolidación.
    """

    def _get_env_api_key(self) -> str | None:
        return config.openrouter_api_key

    def _initialize_client(self) -> OpenAI:
      
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )

    def create_chat_completion(
        self,
        messages: list[dict],
        model: str = "google/gemma-4-31b-it:free",
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> ChatCompletionResponse:
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_headers={
                    "HTTP-Referer": "https://easydocs.local",
                    "X-Title": "EasyDocs",
                }
            )
            
            content = response.choices[0].message.content
            return ChatCompletionResponse(
                choices=[
                    ChatCompletionChoice(
                        message=ChatCompletionMessage(content=content)
                    )
                ]
            )

        except Exception as e:
            # Propaga la excepción original preservando sus atributos (p. ej. .response
            # con el header Retry-After) para que el orquestador detecte rate limits (429).
            # El tipo de excepción de OpenAI ya incluye "rate limit"/"429" en su mensaje.
            if "429" not in str(e).lower() and "rate limit" not in str(e).lower() \
               and "too many requests" not in str(e).lower():
                raise type(e)(f"Error en OpenRouterProvider ({model}): {e}")
            raise