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

    ### Estructura de la Salida:
    1. **Propósito del Módulo**: (Explicación técnica de alto nivel).
    2. **Descripción de Componentes**: (Tabla con Columnas: Campo/Atributo | Tipo de Dato | Descripción).
    3. **Reglas de Negocio Detectadas**: (Listado numerado de las validaciones y procesos lógicos).
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

    ### Contenido Requerido:
    1. Resumen Ejecutivo del Módulo.
    2. Análisis de Estructura (Clases, Funciones y Atributos).
    3. Diagrama Lógico (Descripción textual del flujo).
    4. Reglas de Negocio y Validaciones.

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

    ### Secciones a incluir:
    1. Introducción y Alcance del Código.
    2. Diccionario de Datos (Campos, tipos y propósitos).
    3. Lógica de Negocio y Casos de Uso.
    4. Conclusiones Técnicas para el Informe del SENA.

    ### Código:
    {codigo_fuente}
"""
    
    def generar(self, prompt):
        """
        Genera documentación usando la API de Groq.
        
        Args:
            prompt: Prompt formateado para la IA
            
        Returns:
            str: Contenido generado por la IA
            
        Raises:
            Exception: Si ocurre un error en la llamada a la API
        """
        try:
            logger.info(f"Enviando request a Groq API con modelo: {self.model}")
            
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
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
