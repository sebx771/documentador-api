from google import genai
from google.genai import types
from ....config import config
from .base_provider import BaseAIProvider
from .structures import ChatCompletionResponse, ChatCompletionChoice, ChatCompletionMessage


class GeminiProvider(BaseAIProvider):
    """
    Implementación del proveedor Gemini de Google utilizando el SDK oficial google-genai.
    """

    def _get_env_api_key(self) -> str | None:
        return config.GEMINI_API_KEY

    def _initialize_client(self) -> genai.Client:
        return genai.Client(api_key=self.api_key)

    def create_chat_completion(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> ChatCompletionResponse:
        try:
            system_parts: list[str] = []
            contents: list[types.Content] = []

            for msg in messages:
                role = msg.get("role")
                content = msg.get("content", "")

                if role == "system":
                    system_parts.append(content)
                elif role == "assistant":
                    contents.append(
                        types.Content(
                            role="model",
                            parts=[types.Part.from_text(text=content)],
                        )
                    )
                else:
                    contents.append(
                        types.Content(
                            role="user",
                            parts=[types.Part.from_text(text=content)],
                        )
                    )

            system_instruction = "\n\n".join(system_parts) if system_parts else None

            config_params = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            response = self.client.models.generate_content(
                model=model,
                contents=contents,
                config=config_params,
            )

            text = response.text
            if not text:
                raise ValueError("Respuesta vacía o bloqueada por políticas de seguridad de Gemini")

            return ChatCompletionResponse(
                choices=[
                    ChatCompletionChoice(
                        message=ChatCompletionMessage(content=text)
                    )
                ]
            )

        except Exception as e:
            error_str = str(e).lower()
            # Detecta errores 429 / cuotas de rate limit para re-lanzarlos intactos
            if any(term in error_str for term in ["429", "rate limit", "too many requests", "resource_exhausted"]):
                raise

            # Lanza una excepción genérica preservando el traceback original
            raise RuntimeError(f"Error en GeminiProvider ({model}): {e}") from e