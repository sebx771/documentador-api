# Configuraciones de prompts en Español

ES_STRUCTURE_CHUNK = """
### [Nombre del Módulo/Archivo]
- **Descripción**: Breve resumen técnico (1-2 oraciones).
- **Componentes**: Clases, funciones o estructuras clave.
- **Lógica y Validaciones**: Puntos esenciales del flujo e implementación.
"""

ES_STRUCTURE_FINAL = """
# [Título del Proyecto o Sistema]

## 1. Resumen Ejecutivo
Breve descripción del propósito global del sistema basada estrictamente en el código analizado.

## 2. Arquitectura de Componentes
Tabla consolidada de módulos, responsabilidades y funciones clave presentes en el código.

## 3. Lógica Central y Reglas de Negocio
Explicación detallada de los flujos principales y validaciones.

## 4. Configuración y Errores (Condicional)
Lista de variables de entorno o códigos de error presentes explícitamente en el código. Omitir si no existen.
"""

ES_CONSOLIDATION_PROMPT = """
Actúa como un Editor Técnico Senior. Tu tarea es CONSOLIDAR múltiples fragmentos de documentación en un único documento profesional y coherente.

REGLAS DE ORO:
1. **FACTICIDAD ESTRICTA**: Documenta ÚNICAMENTE lo que esté explícitamente presente en los fragmentos. NO inventes variables de entorno, códigos de error, estados HTTP ni configuraciones.
2. **Deduplicación**: Si varios fragmentos mencionan el mismo componente, únelos en una sola entrada.
3. **Tablas Maestras**: Fusiona todas las tablas de componentes en una SOLA tabla maestra en la Sección 2.
4. **Secciones Condicionales**: Si no hay manejo explícito de errores o variables en el texto, OMITE la sección 4 por completo.
5. **Formato e Idioma**: Sigue estrictamente la estructura (títulos # y ##) de ES_STRUCTURE_FINAL. Responde ÚNICAMENTE en Español.

DOCUMENTO A CONSOLIDAR:
"""

ES_CONFIGS = {
    "markdown": {
        "role": "Ingeniero de Software Senior",
        "objective": "Análisis técnico de un módulo de código para integración en un reporte mayor",
        "format_instructions": """
- Usa Markdown con títulos ## y ###
- Encierra variables y funciones en `código embebido` (IMPORTANTE)
- Mantén un análisis conciso, preciso y fiel al código proporcionado
- Evita frases de relleno o introducciones robóticas.
""",
        "structure": ES_STRUCTURE_FINAL,
    }
}

ES_REFERENCE_TEMPLATE = """
### [X]. Análisis de Componentes (Ejemplo de Referencia)
| Módulo/Clase | Responsabilidad | Funciones Clave / Lógica |
| :--- | :--- | :--- |
| [Nombre] | [Función principal del componente] | [Método clave o flujo de lógica] |
"""

ES_CHUNK_PROMPT = """
MODO FRAGMENTO ACTIVO:
1. PROHIBIDO: No generes títulos de nivel 1 (#), introducciones ni índices.
2. ENFOQUE: Genera un análisis técnico breve siguiendo ES_STRUCTURE_CHUNK.
3. FACTUAL: No asumas lógica fuera de este fragmento. Sé conciso para facilitar la consolidación.
"""