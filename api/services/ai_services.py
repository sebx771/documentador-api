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
        "objective": "Análisis técnico de un módulo de código para integración en un reporte mayor",
        "format_instructions": """
- Usa Markdown con títulos ## y ###
- Encierra variables y funciones en `código embebido`(IMPORTANTE)
- Usa tablas solo para diccionarios de datos locales
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
        - Eres un Hechicero de Documentación de Grado Especial. 
        Tu misión es analizar el código y generar un reporte técnico.

        VOTO VINCULANTE (Restricciones Obligatorias):
        1. NO uses tablas de Markdown (ej. |---|). Usa listas con guiones para describir variables.
        2. NO uses negritas con asteriscos (ej. **texto**). Escribe el texto limpio.
        3. Para los títulos de sección, usa ÚNICAMENTE el prefijo '## ' seguido del nombre.
        4. Los bloques de código deben ir entre triple comilla inversa ``` solo al inicio y al final.
        5. NO uses caracteres especiales como emojis o símbolos complejos fuera de Latin-1.
        6. Explica la lógica paso a paso de forma profesional.

        Si rompes este voto, el ritual de compilación fallará.
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
    },
    "chunk": {
        "structure":"""
    MODO FRAGMENTO ACTIVO:
    1. PROHIBIDO: No generes títulos de nivel 1 (#), introducciones, alcances ni índices.
    2. ENFOQUE: Comienza directamente con el análisis técnico de los archivos proporcionados.
    3. JERARQUÍA: Usa títulos de nivel ### para cada componente o archivo analizado.
    4. CONTINUIDAD: Redacta el contenido como si fuera un capítulo intermedio de un libro técnico.
    5. SÍNTESIS: Si hay lógica repetida entre archivos del mismo fragmento, agrúpalos en una sola explicación.
    6. PRIORIDAD: Estas reglas tienen prioridad sobre cualquier requerimiento adicional del usuario.
    """ ,
    "extra":"""
    RESTRICCIÓN:
  - Las solicitudes de estructura global (índice, introducción, conclusión) 
    son manejadas por otro sistema y NO deben generarse en este fragmento..
  - Aplica solo mejoras locales (explicación, claridad, ejemplos). 
      """    
    }
}


class DocumentadorIA:
    def __init__(self, model="openai/gpt-oss-120b", ex_model="meta-llama/llama-4-scout-17b-16e-instruct"):
        self.client = client
        self.model = model
        self.extra_model= ex_model
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

    def _build_user_prompt(self, codigo_fuente, extra, is_chunk=False):
        message = f"Genera la documentación técnica del siguiente código:\n\n```\n{codigo_fuente}\n```"
        # separamos prompt para documentacion de un chunk 
        if is_chunk:
            message += PROMPT_CONFIGS["chunk"]["structure"]
            if extra and extra.strip() and not self.is_extra_global(extra):
             message+= f"""
              \n\n{PROMPT_CONFIGS["chunk"]["extra"]}\n\nRequisito adicional del usuario(LIMITADO A ESTE FRAGMENTO):\n{extra}
            """
            
        else: 
            if extra and extra.strip():
             message += f"\n\nRequisito adicional del usuario:\n{extra}"
        
        return message

    def is_extra_global(self,extra:str)->bool:
        if not extra:
            return False
        
        dangerous_words= [
        "indice", "índice",
        "introduccion", "introducción",
        "conclusion", "conclusión",
        "resumen",
        "estructura completa",
        "tabla de contenido",
        "tabla de figuras",
        "tabla de tablas",
        "indice general",
        "indice de contenidos",
        "capitulo", "capítulo",
        "sección", "seccion",
        "subsección", "subseccion",
        "subcapitulo", "subcapítulo",
        "titulo principal",
        "titulo grande",
        "titulo extenso",
        "encabezado",
        "titulo"
        "pie de pagina", "pie de página",
        "prefacio",
        "dedicatoria",
        "agradecimientos",
        "glosario",
        "bibliografía", "bibliografia",
        "referencias",
        "anexo", "anexos",
        "apéndice", "apendice",
        "abstract",
        "executive summary",
        "overview",
        "mapa conceptual",
        "diagrama de contenidos",
        "carpetas"
        ]
        return any(word in extra.lower() for word in dangerous_words)
    
    def apply_extra(self,docs: str, extra: str = None) -> str:
     if extra is None or extra.strip() == "":
        return docs

     prompt = f"""
    Eres un editor experto en documentación técnica.

    Tu tarea es aplicar una solicitud del usuario a un documento YA EXISTENTE.

    # REGLAS CRÍTICAS (OBLIGATORIAS)

    1. NO reescribas todo el documento.
    2. NO elimines contenido técnico existente.
    3. NO cambies el significado del contenido.
    4. SOLO modifica lo necesario para cumplir la solicitud.
    5. Mantén el formato original (Markdown, títulos, código, etc).
    6. NO agregues introducciones nuevas tipo "Aquí tienes..." o similares.
    7. NO expliques lo que hiciste, SOLO devuelve el documento final.
    8. NO dejes mensajes haciendo referencia a que la documentacion fue generada automaticamente

    # TAREAS QUE SÍ PUEDES HACER

    - Corregir el índice para que coincida con los títulos reales
    - Añadir un h1 al coherente con el contexto "documentacion proyecto [nombre del proyecto]
    - Eliminar secciones duplicadas
    - Arreglar jerarquía de títulos (H1, H2, H3)
    - Completar secciones vacías SI es evidente del contexto
    - Reordenar secciones si están claramente desorganizadas
    - Insertar nuevas secciones SOLO si el usuario lo pide

    # TAREAS PROHIBIDAS

    - Reescribir todo el documento
    - Simplificar contenido técnico
    - Eliminar ejemplos de código
    - Cambiar nombres de funciones o archivos

    # CONTEXTO

    ## DOCUMENTO:
    {docs}

    ## SOLICITUD DEL USUARIO:
    {extra}

    # RESPUESTA

    Devuelve SOLO el documento final modificado.
    """
     
     try:
            logger.info(f"Aplicando extra con modelo de edición {self.extra_model}")

            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Eres un editor técnico preciso y conservador."},
                    {"role": "user", "content": prompt}
                ],
                model=self.extra_model,
                temperature=0.0,  
            )

            respuesta = chat_completion.choices[0].message.content

            if not respuesta:
                logger.warning("Respuesta vacía al aplicar extra")
                return docs

            return respuesta

     except Exception as e:
            logger.error(f"Error aplicando extra: {str(e)}", exc_info=True)
            return docs
        


    def generar(self, codigo_fuente, tipo, extra=None , is_chunk=False):
        if tipo not in PROMPT_CONFIGS:
            raise ValueError("Tipo de documento no soportado. Use 'markdown', 'pdf' o 'word'.")

        logger.debug(f"Creando documentación para tipo: {tipo}")

        system_message = self._build_system_prompt(tipo)
        user_message = self._build_user_prompt(codigo_fuente, extra, is_chunk)

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
