import logging
import time
import re
from .config import get_groq_client
from .prompts import get_prompts, DANGEROUS_WORDS
from .models import models
from ..rate_limiter import Ratelimiter

logger = logging.getLogger(__name__)

class DocumentadorIA:
    """
    Servicio de IA con Routing Inteligente y Gestión de TPM.
    """
    def __init__(self):
        self.client = get_groq_client()
        self.limiters = {}
        self._init_limiters()
        logger.info("DocumentadorIA v2.3.0 inicializado con Routing y TPM Support")

    def _init_limiters(self):
        """Inicializa un limitador de tokens para cada modelo configurado."""
        for role, config in models.items():
            model_id = config["id"]
            # Usamos el model_id como prefijo para que cada modelo tenga su propio bucket en Redis
            safe_prefix = f"rate:{model_id.replace('/', ':')}"
            self.limiters[model_id] = Ratelimiter(
                tokens_per_min=config["tpm"],
                key_prefix=safe_prefix
            )

    def estimate_tokens(self, system_prompt: str, user_prompt: str) -> int:
        """
        Estimación conservadora de tokens para el par (system + user).
        Heurística: 1 token ≈ 4 caracteres (estándar OpenAI/Groq),
        más un margen de respuesta esperada de 1500 tokens.
        Este valor se usa para verificar el rate limit ANTES de llamar a la API.
        """
        combined = system_prompt + user_prompt
        input_tokens = len(combined) // 4   # 1 token ~ 4 chars (heurística estándar)
        expected_output_tokens = 1500       # Margen de respuesta razonable
        return input_tokens + expected_output_tokens

    def _clean_think_tags(self, text: str) -> str:
        """Elimina las etiquetas <think>...</think> y su contenido de la respuesta."""
        if not text:
            return text
        return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

    def _clean_chunk_instructions(self, text: str) -> str:
        """
        Elimina instrucciones internas del modo-fragmento que el modelo a veces
        repite en su respuesta. Por ejemplo bloques como:
        '**MODO FRAGMENTO ACTIVO** 1. PROHIBIDO...' o
        'ACTIVE CHUNK MODE: 1. FORBIDDEN...'
        """
        if not text:
            return text
        # Patrones de apertura de las instrucciones de chunk (ES y EN)
        patterns = [
            r'\*\*MODO FRAGMENTO ACTIVO\*\*.*?(?=#{1,4} |\Z)',
            r'MODO FRAGMENTO ACTIVO:.*?(?=#{1,4} |\Z)',
            r'\*\*ACTIVE CHUNK MODE\*\*.*?(?=#{1,4} |\Z)',
            r'ACTIVE CHUNK MODE:.*?(?=#{1,4} |\Z)',
        ]
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.DOTALL)
        return text.strip()

    def generar(self, codigo_fuente, tipo, extra=None, is_chunk=False, lang=None, model_role=None):
        """
        Punto de entrada con Routing y Fallback.
        """
        if lang is None:
            lang = self.detect_language(codigo_fuente, extra)
        
        # 1. Determinar el modelo inicial basado en el rol (chunking o final)
        if not model_role:
            model_role = "chunking" if is_chunk else "final_doc"
        
        target_model = models[model_role]["id"]
        
        # Intentar con fallback si el principal falla
        retry_queue = [
            models["final_doc"]["id"] if not is_chunk else models["chunking"]["id"],
            models["fallback"]["id"],
            models["emergency"]["id"]
        ]
        # Eliminar duplicados manteniendo el orden
        retry_queue = list(dict.fromkeys(retry_queue))

        system_message = self._build_system_prompt(tipo, lang)
        user_message = self._build_user_prompt(codigo_fuente, extra, lang, is_chunk)
        
        # Estimar tokens UNA VEZ (no cambia entre reintentos del mismo prompt)
        tokens_needed = self.estimate_tokens(system_message, user_message)
        logger.info(f"Tokens estimados para esta petición: {tokens_needed}")

        last_error = None
        for current_model in retry_queue:
            try:
                # 2. Gestión de Rate Limit (TPM)
                limiter = self.limiters.get(current_model)
                model_tpm = next(
                    (cfg["tpm"] for cfg in models.values() if cfg["id"] == current_model),
                    None
                )

                # Si la petición por sí sola supera el TPM del modelo, ni intentamos
                if model_tpm and tokens_needed > model_tpm:
                    logger.warning(
                        f"Petición ({tokens_needed} tk) supera el TPM de {current_model} ({model_tpm} tk/min). "
                        f"Saltando directamente al siguiente modelo."
                    )
                    continue

                if limiter:
                    logger.info(f"Solicitando {tokens_needed} tokens para modelo {current_model}...")
                    if not limiter.allow_request(tokens_needed):
                        logger.warning(f"Rate limit local excedido para {current_model}. Saltando al siguiente modelo.")
                        continue

                logger.info(f"Llamando a {current_model} (Rol: {model_role}, Lang: {lang})")
                
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    model=current_model,
                    temperature=0.1 if not is_chunk else 0.2,
                )

                respuesta = chat_completion.choices[0].message.content
                if not respuesta:
                    raise Exception("Respuesta vacía de la API")

                # 3. Limpieza de tags de razonamiento (ej. Qwen) + instrucciones de chunk
                respuesta_limpia = self._clean_think_tags(respuesta)
                respuesta_limpia = self._clean_chunk_instructions(respuesta_limpia)
                return respuesta_limpia

            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                if "429" in error_str or "rate limit" in error_str or "too many requests" in error_str:
                    logger.warning(f"MODEL FAILOVER: {current_model} reportó 429. Reintentando con el siguiente...")
                    time.sleep(2) # Pequeña espera antes de saltar
                    continue
                else:
                    logger.error(f"Error crítico en {current_model}: {e}")
                    raise e
        
        raise Exception(f"Todos los modelos de la cola fallaron. Último error: {last_error}")

    def detect_language(self, code: str, extra: str) -> str:
        text = (code + " " + (extra or "")).lower()
        es_score = sum(text.count(word) for word in [" de ", " para ", " funciones ", " archivo ", " el ", " la "])
        en_score = sum(text.count(word) for word in [" of ", " for ", " functions ", " file ", " the ", " a "])
        return "en" if en_score > es_score else "es"

    def _build_system_prompt(self, tipo: str, lang: str):
        prompts = get_prompts(lang)
        config = prompts["configs"].get(tipo, prompts["configs"]["markdown"])
        # La instrucción de idioma va PRIMERO para que el modelo le dé maxima prioridad
        lang_instruction = "RESPOND ONLY IN ENGLISH. All output must be in English." if lang == "en" else "RESPONDE ÚNICAMENTE EN ESPAÑOL. Todo el output debe estar en español."
        system_prompt = f"""{lang_instruction}

Actúa como un {config['role']}.
Tu tarea es analizar código fuente y generar {config['objective']}.
Instrucciones de formato:
{config['format_instructions']}
Reglas obligatorias:
- No uses frases como "este código" o "el código proporcionado"
- No expliques cómo se generó la documentación
- Enfócate solo en el resultado final
- {lang_instruction}
{config['structure']}
"""
        if tipo == "markdown":
            system_prompt += f"\n\n### EJEMPLO DE ESTÁNDAR VISUAL:\n{prompts['reference']}"
        return system_prompt

    def _build_user_prompt(self, codigo_fuente, extra, lang, is_chunk=False):
        prompts = get_prompts(lang)
        if lang == "en":
            instr = f"Generate the technical documentation for the following code:\n\n```\n{codigo_fuente}\n```"
            extra_prefix = "\n\nAdditional user requirements:"
        else:
            instr = f"Genera la documentación técnica del siguiente código:\n\n```\n{codigo_fuente}\n```"
            extra_prefix = "\n\nRequisito adicional del usuario:"
        # Refuerzo de idioma al FINAL del user message (los LLM prestan atención al inicio Y al final)
        lang_reminder = "\n\n[IMPORTANT: Your entire response must be written ONLY in English.]" if lang == "en" else "\n\n[IMPORTANTE: Tu respuesta completa debe estar Únicamente en español.]"
        message = instr
        if is_chunk:
            message += f"\n\n{prompts['chunk']}"
            if extra and extra.strip() and not self.is_extra_global(extra):
                message += f"{extra_prefix} (LIMITADO A ESTE FRAGMENTO):\n{extra}"
        else:
            if extra and extra.strip():
                message += f"{extra_prefix}\n{extra}"
        message += lang_reminder
        return message

    def is_extra_global(self, extra: str) -> bool:
        if not extra: return False
        extra_lower = extra.lower()
        for lang in DANGEROUS_WORDS:
            if any(word in extra_lower for word in DANGEROUS_WORDS[lang]):
                return True
        return False
    
    def apply_extra(self, docs: str, extra: str = None, lang: str = None) -> str:
        """Aplica requisitos extras al documento final, respetando el idioma original."""
        if not extra or not extra.strip(): return docs
        return self.generar(docs, "markdown", extra=extra, is_chunk=False, model_role="final_doc", lang=lang)
