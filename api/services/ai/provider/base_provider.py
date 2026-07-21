from abc import ABC, abstractmethod
from .structures import ChatCompletionResponse

class BaseAIProvider(ABC):
    """
    Clase padre abstracta que define el contrato mínimo para los proveedores de IA.
    Permite la sustitución de Groq por Cerebras, OpenAI, Qwen, etc.
    """
    
    def __init__(self, api_key: str = None) -> None:
        """
        Inicializa el cliente del proveedor e implementa las validaciones del contrato.
        """
       
        self.api_key = api_key or self._get_env_api_key()
        
        if not self.api_key:
            raise ValueError(
                f"Error de configuración: No se encontró la API Key para el proveedor {self.__class__.__name__}."
            )
        
       
        try:
            self.client = self._initialize_client()
        except Exception as e:
            raise Exception(f"Fallo crítico al inicializar el cliente SDK de {self.__class__.__name__}: {str(e)}")

    @abstractmethod
    def _get_env_api_key(self) -> str | None:
        """
        Retorna la variable de entorno específica de cada proveedor (ej. GROQ_API_KEY).
        """
        pass

    @abstractmethod
    def _initialize_client(self) -> any:
        """
        Instancia el SDK nativo correspondiente del proveedor.
        """
        pass

    @abstractmethod
    def create_chat_completion(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> ChatCompletionResponse:
        """
        Envía los mensajes al modelo del proveedor y retorna una estructura compatible
        con `.choices[0].message.content`.
        
        Debe lanzar excepciones legibles que contengan '429', 'rate limit' o 
        'too many requests' si el proveedor responde con saturación de tasa.
        """
        pass


