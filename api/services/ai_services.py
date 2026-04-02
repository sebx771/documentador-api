import os
from groq import Groq
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv()

api_key = os.getenv("API_KEY")
if not api_key:
    logger.error("API_KEY no encontrada en variables de entorno")
    raise ValueError("API_KEY no configurada. Configure la variable de entorno API_KEY")

try:
    client = Groq(api_key=api_key)
    logger.info("Cliente Groq inicializado correctamente")
except Exception as e:
    logger.error(f"Error al inicializar cliente Groq: {str(e)}")
    raise

PROMPT_CONFIGS = {
    "markdown": {
        "role": "Ingeniero de Software Senior",
        "objective": "documentación técnica detallada para un informe ",
        "format_instructions": """
- Usa Markdown con títulos ## y ###
- Encierra variables y funciones en `código embebido`
- Usa tablas para campos/atributos cuando existan
- Usa listas con viñetas para reglas de negocio
- Adapta el nivel de detalle según la complejidad del código
- Omite tablas si no hay campos que documentar
- Usa un lenguaje técnico pero natural, evitando sonar robótico o excesivamente formal.
""",
        "structure": """
### Estructura requerida:
0. # Título: Documentación Técnica de Módulo "[nombre]"
1. ## 1. Definición y Alcance
2. ## 2. Arquitectura de Componentes (Tabla de Diccionario de Datos)
3. ## 3. Lógica de Negocio y Validaciones
4. ## 4. Guía de Integración (Ejemplo de Uso con JSON)
5. ## 5,6,7...  temas a criterio de la IA (opcional, solo si el código tiene aspectos complejos o relevantes que no encajan en las secciones anteriores)
"""
    },
    "pdf": {
        "role": "Ingeniero de Software Senior",
        "objective": "Informe Técnico Formal para exportación a PDF",
        "format_instructions": """
- Usa jerarquía clara (1.0, 1.1, 2.0)
- Presenta atributos en tablas comparativas
- Lenguaje técnico, formal y descriptivo
- Adapta el nivel de detalle según la complejidad del código
- Usa un lenguaje técnico pero natural, evitando sonar robótico o excesivamente formal.
""",
        "structure": """
### Secciones requeridas:
1. Introducción y Alcance del Código
2. Diccionario de Datos (Campos, tipos y propósitos)
3. Lógica de Negocio y Casos de Uso
4. Conclusiones Técnicas para el Informe
"""
    },
    "word": {
        "role": "Analista de Desarrollo de Software",
        "objective": "Documento de Requerimientos Técnicos en Microsoft Word",
        "format_instructions": """
- Genera descripciones detalladas y extensas
- Estructura con títulos claros de secciones Word
- Incluye Glosario Técnico si hay términos complejos
- Redacta reglas de negocio como requerimientos funcionales
- Adapta el nivel de detalle según la complejidad del código
- Usa un lenguaje técnico pero natural, evitando sonar robótico o excesivamente formal.
""",
        "structure": """
### Secciones requeridas:
1. Introducción y Alcance del Código
2. Diccionario de Datos (Campos, tipos y propósitos)
3. Lógica de Negocio y Casos de Uso
4. Conclusiones Técnicas para el Informe
"""
    }
}


class DocumentadorIA:
    def __init__(self, model="llama-3.3-70b-versatile"):
        self.client = client
        self.model = model
        logger.info(f"DocumentadorIA inicializado con modelo: {model}")

    def _build_system_prompt(self, tipo):
        config = PROMPT_CONFIGS[tipo]
        return f"""Actúa como un {config['role']}.

Tu tarea es analizar código fuente y generar {config['objective']}.

Instrucciones de formato:
{config['format_instructions']}

Reglas obligatorias:
- No uses frases como "este código" o "el código proporcionado"
- No expliques cómo se generó la documentación
- Enfócate solo en el resultado final

{config['structure']}"""

    def _build_user_prompt(self, codigo_fuente, extra):
        message = f"Genera la documentación técnica del siguiente código:\n\n```\n{codigo_fuente}\n```"
        
        if extra and extra.strip():
            message += f"\n\nRequisito adicional del usuario:\n{extra}"
        
        return message

    def generar(self, codigo_fuente, tipo, extra=None):
        if tipo not in PROMPT_CONFIGS:
            raise ValueError("Tipo de documento no soportado. Use 'markdown', 'pdf' o 'word'.")

        logger.debug(f"Creando documentación para tipo: {tipo}")

        system_message = self._build_system_prompt(tipo)
        user_message = self._build_user_prompt(codigo_fuente, extra)

        try:
            logger.info(f"Enviando request a Groq API con modelo: {self.model}")

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
                logger.warning("La API de Groq devolvió una respuesta vacía")
                raise Exception("La API devolvió una respuesta vacía")

            logger.info(f"Documentación generada exitosamente ({len(respuesta)} caracteres)")
            return respuesta

        except Exception as e:
            logger.error(f"Error en llamada a Groq API: {str(e)}", exc_info=True)
            raise Exception(f"Error al generar documentación: {str(e)}")
