import os
from groq import Groq
from dotenv import load_dotenv
import logging

# Configurar logging
logger = logging.getLogger(__name__)

load_dotenv()  # Carga las variables de entorno desde el archivo .env

# Validar que la API key esté configurada
api_key = os.getenv("API_KEY")
if not api_key:
    logger.error("API_KEY no encontrada en variables de entorno")
    raise ValueError("API_KEY no configurada. Configure la variable de entorno API_KEY")

# Variables globales
## Markdown
formato_salida = """
### 🏗️ ESTRUCTURA TÉCNICA DE LA SALIDA (OBLIGATORIO):
    1. **## 1. Definición y Alcance**: 
       - Describe el propósito del módulo. 
       - Menciona el stack tecnológico detectado (ej: `Flask`, `Pydantic`, `Logging`).
    
    2. **## 2. Arquitectura de Componentes**: 
       - Presenta una **Tabla de Diccionario de Datos** con: `Entidad/Variable`, `Tipo`, `Descripción` y `Valor por Defecto`.
       - Usa `código embebido` para cada nombre técnico.
    
    3. **## 3. Lógica de Negocio y Validaciones**: 
       - Lista numerada de procesos lógicos.
       - Detalla restricciones específicas (ej: "El `codigo` debe tener entre `MIN_CODE_LENGTH` y `MAX_CODE_LENGTH` caracteres").
    
    4. **## 4. Guía de Integración (Ejemplo de Uso)**: 
       - Incluye un bloque de código con un ejemplo de petición `POST` en formato `JSON`.
       - Muestra un ejemplo de la respuesta generada.
"""
## PDF
formato_salida_pdf = """
 ### Secciones a incluir:
    1. Introducción y Alcance del Código.
    2. Diccionario de Datos (Campos, tipos y propósitos).
    3. Lógica de Negocio y Casos de Uso.
    4. Conclusiones Técnicas para el Informe.
"""
## Word
formato_salida_word = """
    ### Secciones a incluir:
    1. Introducción y Alcance del Código.
    2. Diccionario de Datos (Campos, tipos y propósitos).
    3. Lógica de Negocio y Casos de Uso.
    4. Conclusiones Técnicas para el Informe.
"""


try:
    client = Groq(api_key=api_key)
    logger.info("Cliente Groq inicializado correctamente")
except Exception as e:
    logger.error(f"Error al inicializar cliente Groq: {str(e)}")
    raise

class DocumentadorIA:
    def __init__(self, model="llama-3.3-70b-versatile"):
        self.client = client
        self.model = model
        logger.info(f"DocumentadorIA inicializado con modelo: {model}")
    
    def _crear_prompt(self, codigo_fuente, tipo) -> str:
        """
        Crea el prompt para generar documentación según el tipo especificado.
        
        Args:
            codigo_fuente: Código fuente a documentar
            tipo: Tipo de documento ('markdown', 'pdf', 'word')
            
        Returns:
            str: Prompt formateado para la IA
            
        Raises:
            ValueError: Si el tipo no es soportado
        """
        if tipo not in ["markdown", "pdf", "word"]:
            raise ValueError("Tipo de documento no soportado. Use 'markdown', 'pdf' o 'word'.")
        
        logger.debug(f"Creando prompt para tipo: {tipo}")

        if tipo == "markdown":
            return f"""
       Actúa como un Ingeniero de Software experto de nivel Senior. 
    Analiza el siguiente código fuente y genera una **documentación técnica detallada** para un informe del SENA.
    
    ### Instrucciones de Formato (ESTRICTO):
    1. Usa **Markdown** para toda la respuesta.
    2. Utiliza títulos de nivel 2 y 3 (## y ###) para las secciones.
    3. Los nombres de variables o funciones deben ir en `código embebido`.
    4. Si hay campos o atributos, utiliza una **Tabla de Markdown** para describirlos.
    5. Usa listas con viñetas para las reglas de negocio.
    6. Evita expresiones referidas a "este código", "el codigo proporcionado" o "el código anterior". Sé específico en la descripción.
    7. No incluyas explicaciones sobre cómo se generó la documentación, solo el resultado final.
    8. si no se detectan campos o atributos, omite la tabla y solo describe la lógica de negocio.
    ### Código a analizar:
    ```
    {codigo_fuente}
    ```
    {formato_salida}
    """
        elif tipo == "pdf":
            return f"""
Actúa como un Ingeniero de Software Senior. 
    Analiza el siguiente código y genera un **Informe Técnico Formal** apto para exportación a PDF.
    
    ### Instrucciones de Formato (ESTRICTO):
      1. Evita expresiones referidas a "este código", "el codigo proporcionado" o "el código anterior". Sé específico en la descripción.
    2. No incluyas explicaciones sobre cómo se generó la documentación, solo el resultado final.

    ### Estructura del Informe (Formato Profesional):
    - Título Principal: Documentación Técnica de Módulo.
    - Encabezados: Usa jerarquía clara (1.0, 1.1, 2.0).
    - Tablas: Presenta los atributos/campos en una tabla comparativa.
    - Párrafos: Usa un lenguaje descriptivo, técnico y formal.

    {formato_salida_pdf}

    ### Código:
    {codigo_fuente}
    """
        elif tipo == "word":
            return f""" 
Actúa como un Analista de Desarrollo de Software. 
    Genera el contenido para un **Documento de Requerimientos Técnicos** en Microsoft Word.
    
   ### Instrucciones de Formato (ESTRICTO):
     1. Evita expresiones referidas a "este código", "el codigo proporcionado" o "el código anterior". Sé específico en la descripción.
    2. No incluyas explicaciones sobre cómo se generó la documentación, solo el resultado final.

    ### Instrucciones de Estilo:
    - Genera descripciones detalladas y extensas (evita respuestas cortas).
    - Estructura el contenido con títulos claros que correspondan a secciones de un documento de Word.
    - Incluye una sección de 'Glosario Técnico' si detectas términos complejos.
    - Asegúrate de que las reglas de negocio estén redactadas como requerimientos funcionales.

   
     {formato_salida_word}

    ### Código:
    {codigo_fuente}
"""
    
    def generar(self, prompt):

        try:
            logger.info(f"Enviando request a Groq API con modelo: {self.model}")
            
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
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
