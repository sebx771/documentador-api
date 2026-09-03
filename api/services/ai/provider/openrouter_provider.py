from openai import OpenAI
from api.config import config
from .base_provider import BaseAIProvider
from .structures import ChatCompletionResponse

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
            return ChatCompletionResponse(content=content, raw_response=response)

        except Exception as e:
            # Preserva el mensaje de error para que el orquestador detecte rate limits (429)
            raise Exception(f"Error en OpenRouterProvider ({model}): {str(e)}")