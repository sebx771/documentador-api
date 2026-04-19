import logging
from .config import get_groq_client
from .prompts import get_prompts, DANGEROUS_WORDS

logger = logging.getLogger(__name__)

class DocumentadorIA:
    """
    Servicio de inteligencia artificial para generar documentación, DE VERDAD ESTAS LEYENDO ESTO?
    Soporta múltiples idiomas con detección inteligente y procesamiento por fragmentos.
    """
    def __init__(self, model="openai/gpt-oss-120b", ex_model="meta-llama/llama-4-scout-17b-16e-instruct"):
        self.client = get_groq_client()
        self.model = model
        self.extra_model = ex_model
        logger.info(f"DocumentadorIA modular inicializado con modelo: {model}")

    def detect_language(self, code: str, extra: str) -> str:
        """
        Heurística(jajaaja xd) simple para detectar si el usuario prefiere español o inglés.
        """
        text = (code + " " + (extra or "")).lower()
        
        # Pesos para palabras comunes
        es_score = sum(text.count(word) for word in [" de ", " para ", " funciones ", " archivo ", " el ", " la "])
        en_score = sum(text.count(word) for word in [" of ", " for ", " functions ", " file ", " the ", " a "])
        
        lang = "en" if en_score > es_score else "es"
        logger.info(f"Idioma detectado: {lang} (ES score: {es_score}, EN score: {en_score})")
        return lang

    def _build_system_prompt(self, tipo: str, lang: str):
        """
        Construye el prompt de sistema basado en el tipo de doc e idioma.
        """
        prompts = get_prompts(lang)
        config = prompts["configs"].get(tipo, prompts["configs"]["markdown"])
        
        system_prompt = f"""Actúa como un {config['role']}.

Tu tarea es analizar código fuente y generar {config['objective']}.

Instrucciones de formato:
{config['format_instructions']}

Reglas obligatorias:
- No uses frases como "este código" o "el código proporcionado"
- No expliques cómo se generó la documentación
- Enfócate solo en el resultado final
- RESPONDE ÚNICAMENTE EN { 'INGLÉS' if lang == 'en' else 'ESPAÑOL' }.

{config['structure']}
"""
        # Inyectar ejemplo visual si es Markdown
        if tipo == "markdown":
            system_prompt += f"\n\n### EJEMPLO DE ESTÁNDAR VISUAL:\n{prompts['reference']}"

        return system_prompt

    def _build_user_prompt(self, codigo_fuente, extra, lang, is_chunk=False):
        """
        Construye el prompt del usuario con el código y requisitos extra.
        """
        prompts = get_prompts(lang)
        
        if lang == "en":
            instr = f"Generate the technical documentation for the following code:\n\n```\n{codigo_fuente}\n```"
            extra_prefix = "\n\nAdditional user requirements:"
        else:
            instr = f"Genera la documentación técnica del siguiente código:\n\n```\n{codigo_fuente}\n```"
            extra_prefix = "\n\nRequisito adicional del usuario:"

        message = instr
        
        if is_chunk:
            message += f"\n\n{prompts['chunk']}"
            if extra and extra.strip() and not self.is_extra_global(extra):
                message += f"{extra_prefix} (LIMITADO A ESTE FRAGMENTO):\n{extra}"
        else:
            if extra and extra.strip():
                message += f"{extra_prefix}\n{extra}"
        
        return message

    def is_extra_global(self, extra: str) -> bool:
        """Determina si el requisito adicional afecta a la estructura global."""
        if not extra:
            return False
        
        extra_lower = extra.lower()
        # Verificar en ambos idiomas
        for lang in DANGEROUS_WORDS:
            if any(word in extra_lower for word in DANGEROUS_WORDS[lang]):
                return True
        return False
    
    def apply_extra(self, docs: str, extra: str = None) -> str:
        """
        Aplica consolidación final y requisitos globales al documento unido.
        Detecta el idioma predominante del documento consolidado.
        """
        if extra is None or extra.strip() == "":
            return docs

        # Detectar idioma para los prompts de edición
        lang = self.detect_language(docs, extra)
        p = get_prompts(lang)

        prompt = f"""
        {p['edit_role']}
        {p['edit_instruction']}

        # REGLAS CRÍTICAS (OBLIGATORIAS)
        1. NO reescribas todo el documento.
        2. NO elimines contenido técnico existente.
        3. Mantén el formato original (Markdown, títulos, código, etc).
        4. SOLO devuelve el documento final.
        5. Asegúrate de añadir un título principal ({p['final_title']}) si no existe.

        # CONTEXTO
        ## DOCUMENTO:
        {docs}

        ## SOLICITUD DEL USUARIO:
        {extra}

        # RESPUESTA
        Devuelve SOLO el documento final modificado en { 'INGLÉS' if lang == 'en' else 'ESPAÑOL' }.
        """
        
        try:
            logger.info(f"Aplicando consolidación con modelo {self.extra_model} en idioma: {lang}")

            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": p['edit_system']},
                    {"role": "user", "content": prompt}
                ],
                model=self.extra_model,
                temperature=0.0,  
            )

            respuesta = chat_completion.choices[0].message.content
            return respuesta or docs

        except Exception as e:
            logger.error(f"Error aplicando extra: {str(e)}")
            return docs

    def generar(self, codigo_fuente, tipo, extra=None, is_chunk=False, lang=None):
        """
        Punto de entrada principal para generar documentación.
        """
        if lang is None:
            # 1. Detectar idioma inteligentemente
            lang = self.detect_language(codigo_fuente, extra)
        
        # Construimos prompts
        system_message = self._build_system_prompt(tipo, lang)
        user_message = self._build_user_prompt(codigo_fuente, extra, lang, is_chunk)

        try:
            logger.info(f"Generando documentation en {lang} con {self.model}")

            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                model=self.model,
                temperature=0.1,
            )

            respuesta = chat_completion.choices[0].message.content
            if not respuesta:
                raise Exception("La API devolvió una respuesta vacía")

            return respuesta

        except Exception as e:
            logger.error(f"Error en AI Service: {str(e)}")
            raise
