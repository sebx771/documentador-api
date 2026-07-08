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
        logger.info("DocumentadorIA v2.3.1 inicializado con Routing y TPM Support")

    def _init_limiters(self):
        """Inicializa un limitador de tokens para cada modelo configurado."""
        for role, config in models.items():
            model_id = config["id"]
            model_tpm = config["tpm"]
            # Usamos el model_id como prefijo para que cada modelo tenga su propio bucket en Redis
            safe_prefix = f"rate:{model_id.replace('/', ':')}"
            self.limiters[model_id] = {
                "ratelimiter": Ratelimiter(
                    tokens_per_min=config["tpm"], key_prefix=safe_prefix
                ),
                "tpm": model_tpm,
            }

    def estimate_tokens(self, system_prompt: str, user_prompt: str) -> int:
        """
        Estimación mejorada de tokens para el par (system + user).

        Heurística:
        - Input: 1 token ≈ 3.5 caracteres (más preciso que 4)
        - Output: Estimamos 30-50% del tamaño de input (varía según complejidad)

        Esta estimación se usa para verificar rate limits ANTES de llamar a API.
        """
        system_len = len(system_prompt)
        user_len = len(user_prompt)

        # Estimación de input tokens (más preciso)
        input_tokens = int((system_len + user_len) / 3.5)

        # Estimación de output tokens (adaptativo)
        # Documentación típica: 40-60% del tamaño del input
        # Chunks: 30-40% del input
        # Final docs: 50-60% del input
        # Promedio conservador: 45%
        expected_output_tokens = max(500, int(input_tokens * 0.45))

        total = input_tokens + expected_output_tokens

        logger.debug(
            f"Token estimation: input={system_len + user_len} chars → "
            f"{input_tokens} input tokens + {expected_output_tokens} output tokens = {total} total"
        )

        return total

    def _clean_think_tags(self, text: str) -> str:
        """Elimina las etiquetas <think>...</think> y su contenido de la respuesta."""
        if not text:
            return text
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

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
            r"\*\*MODO FRAGMENTO ACTIVO\*\*.*?(?=#{1,4} |\Z)",
            r"MODO FRAGMENTO ACTIVO:.*?(?=#{1,4} |\Z)",
            r"\*\*ACTIVE CHUNK MODE\*\*.*?(?=#{1,4} |\Z)",
            r"ACTIVE CHUNK MODE:.*?(?=#{1,4} |\Z)",
        ]
        for pattern in patterns:
            text = re.sub(pattern, "", text, flags=re.DOTALL)
        return text.strip()

    def generar(
        self,
        codigo_fuente:str,
        tipo:str,
        extra:str=None,
        is_chunk:bool=False,
        lang:str=None,
        model_role:str=None,
    ):
        """
        Punto de entrada con Routing y Fallback.
        """
        if lang is None:
            lang = self.detect_language(codigo_fuente, extra)

        # 1. Determinar el modelo inicial basado en el rol (chunking o final)
        if not model_role:
            model_role = "chunking" if is_chunk else "final_doc"

        # Intentar con fallback si el principal falla
        retry_queue = [
            models["final_doc"]["id"] if not is_chunk else models["chunking"]["id"],
            models["fallback"]["id"],
            models["emergency"]["id"]
        ]
        # Eliminar duplicados manteniendo el orden
        retry_queue = list(dict.fromkeys(retry_queue))

        system_message = self._build_system_prompt(
            tipo,
            lang,
            is_chunk=is_chunk,
            is_consolidation=(model_role == "final_doc" and not is_chunk),
        )
        user_message = self._build_user_prompt(codigo_fuente, extra, lang, is_chunk)

        # Estimar tokens UNA VEZ (no cambia entre reintentos del mismo prompt)
        tokens_needed = self.estimate_tokens(system_message, user_message)
        logger.info(f"Tokens estimados para esta petición: {tokens_needed}")

        last_error = None
        for current_model in retry_queue:
            # Reintentar el mismo modelo tras backoff si el rate limiter bloquea
            model_retries = 3
            for attempt in range(model_retries):
                try:
                    limiter = self.limiters.get(current_model, {}).get("ratelimiter")
                    model_tpm = self.limiters.get(current_model, {}).get("tpm")

                    if model_tpm and tokens_needed > model_tpm:
                        logger.warning(
                            f"Petición ({tokens_needed} tk) supera el TPM de {current_model} ({model_tpm} tk/min). "
                            f"Saltando al siguiente modelo."
                        )
                        last_error = Exception(
                            f"Petición ({tokens_needed} tk) excede el TPM ({model_tpm} tk) de {current_model}"
                        )
                        break

                    if limiter and not limiter.allow_request(tokens_needed):
                        if attempt < model_retries - 1:
                            wait = 1 * (2 ** attempt)
                            logger.warning(
                                f"Rate limit local excedido para {current_model}. "
                                f"Reintento {attempt + 1}/{model_retries} en {wait}s..."
                            )
                            time.sleep(wait)
                            continue
                        else:
                            logger.warning(
                                f"Rate limit local excedido para {current_model} "
                                f"tras {model_retries} intentos. Saltando al siguiente modelo."
                            )
                            last_error = Exception(
                                f"Rate limit excedido para {current_model} tras {model_retries} intentos"
                            )
                            break

                    logger.info(
                        f"Llamando a {current_model} (Rol: {model_role}, Lang: {lang})"
                    )

                    max_output_tokens = 4096 if (not is_chunk or model_role == "final_doc") else 2048

                    chat_completion = self.client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": user_message},
                        ],
                        model=current_model,
                        temperature=0.1 if not is_chunk else 0.2,
                        max_tokens=max_output_tokens,
                    )

                    respuesta = chat_completion.choices[0].message.content
                    if not respuesta:
                        raise Exception("Respuesta vacía de la API")

                    respuesta_limpia = self._clean_think_tags(respuesta)
                    respuesta_limpia = self._clean_chunk_instructions(respuesta_limpia)
                    return respuesta_limpia

                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()
                    if (
                        "429" in error_str
                        or "rate limit" in error_str
                        or "too many requests" in error_str
                    ):
                        if attempt < model_retries - 1:
                            wait = 1 * (2 ** attempt)
                            logger.warning(
                                f"429 en {current_model}. Reintento {attempt + 1}/{model_retries} en {wait}s..."
                            )
                            time.sleep(wait)
                            continue
                        else:
                            logger.warning(
                                f"MODEL FAILOVER: {current_model} reportó 429 tras {model_retries} intentos. "
                                f"Saltando al siguiente modelo."
                            )
                            time.sleep(2)
                            break
                    else:
                        logger.error(f"Error crítico en {current_model}: {e}")
                        raise e

        raise Exception(
            f"Todos los modelos de la cola fallaron. Último error: {last_error}"
        )

    def detect_language(self, code: str, extra: str) -> str:
        text = (code + " " + (extra or "")).lower()
        es_score = sum(
            text.count(word)
            for word in [" de ", " para ", " funciones ", " archivo ", " el ", " la "]
        )
        en_score = sum(
            text.count(word)
            for word in [" of ", " for ", " functions ", " file ", " the ", " a "]
        )
        return "en" if en_score > es_score else "es"

    def _build_system_prompt(
        self,
        tipo: str,
        lang: str,
        is_chunk: bool = False,
        is_consolidation: bool = False,
    )-> str:
        prompts = get_prompts(lang)
        config = prompts["configs"].get(tipo, prompts["configs"]["markdown"])

        # 1. Determinar el idioma base
        lang_instruction = (
            "RESPOND ONLY IN ENGLISH. All output must be in English."
            if lang == "en"
            else "RESPONDE ÚNICAMENTE EN ESPAÑOL. Todo el output debe estar en español."
        )

        # 2. Selección de estructura
        if is_consolidation:
            return f"{lang_instruction}\n\n{prompts['consolidation']}"

        structure = prompts["chunk_structure"] if is_chunk else config["structure"]

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

### Estructura a seguir:
{structure}
"""
        if tipo == "markdown" and not is_chunk:
            system_prompt += (
                f"\n\n### EJEMPLO DE ESTÁNDAR VISUAL:\n{prompts['reference']}"
            )
        return system_prompt

    def _build_user_prompt(self, codigo_fuente:str, extra:str, lang:str, is_chunk:bool=False)-> str:
        prompts = get_prompts(lang)
        if lang == "en":
            instr = f"Generate the technical documentation for the following code:\n\n```\n{codigo_fuente}\n```"
            extra_prefix = "\n\nAdditional user requirements:"
        else:
            instr = f"Genera la documentación técnica del siguiente código:\n\n```\n{codigo_fuente}\n```"
            extra_prefix = "\n\nRequisito adicional del usuario:"
        # Refuerzo de idioma al FINAL del user message (los LLM prestan atención al inicio Y al final)
        lang_reminder = (
            "\n\n[IMPORTANT: Your entire response must be written ONLY in English.]"
            if lang == "en"
            else "\n\n[IMPORTANTE: Tu respuesta completa debe estar Únicamente en español.]"
        )
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
        if not extra:
            return False
        extra_lower = extra.lower()
        for lang in DANGEROUS_WORDS:
            if any(word in extra_lower for word in DANGEROUS_WORDS[lang]):
                return True
        return False

    def apply_extra(self, docs: str, extra: str = None, lang: str = None) -> str:
        """Aplica requisitos extras al documento final, respetando el idioma original."""
        logger.info("Aplicando requisitos extra a la documentación")
        if not extra or not extra.strip():
            return docs

        # Estimar tokens y validar que cabe en el modelo final_doc
        estimated_tokens = len(docs) // 3
        final_tpm = models.get("final_doc", {}).get("tpm", 8000)
        if estimated_tokens > final_tpm:
            logger.warning(
                f"Documento consolidado muy grande ({estimated_tokens} tk estimados) "
                f"para final_doc ({final_tpm} TPM). Omitiendo apply_extra "
                f"para evitar error masivo. El extra se perderá."
            )
            return docs

        return self.generar(
            docs,
            tipo="markdown",
            extra=extra,
            is_chunk=False,
            model_role="final_doc",
            lang=lang,
        )

    def consolidate(self, docs: str, lang: str = "es") -> str:
        """
        Realiza una pasada final de IA para consolidar tablas, deduplicar
        y unificar el estilo de la documentación.
        """
        logger.info(f"Iniciando consolidación final de IA (Lang: {lang})")
        return self.generar(
            codigo_fuente=docs,
            tipo="markdown",
            is_chunk=False,
            model_role="final_doc",
            lang=lang,
        )
