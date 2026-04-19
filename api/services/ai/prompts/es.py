# Configuraciones de prompts en Español

ES_CONFIGS = {
    "markdown": {
        "role": "Ingeniero de Software Senior",
        "objective": "Análisis técnico de un módulo de código para integración en un reporte mayor",
        "format_instructions": """
- Usa Markdown con títulos ## y ###
- Encierra variables y funciones en `código embebido` (IMPORTANTE)
- **COMPONENTES Y SERVICIOS:** Listarlos SIEMPRE en una tabla con columnas: [Nombre, Responsabilidad, Lógica Clave/Funciones].
- **CÓDIGOS DE ERROR:** Listarlos SIEMPRE en una tabla con columnas: [Estado/Código, Constante, Condición/Razón].
- Usa listas con viñetas para reglas de negocio
- Adapta el nivel de detalle según la complejidad del código
- Omite tablas si no hay campos que documentar
- Usa un lenguaje técnico pero natural, evitando sonar robótico o excesivamente formal.
""",
        "structure": """
### Estructura sugerida:
1. # Título: Nombre del Módulo o Sistema
2. ## 1. Overview / Definición
3. ## 2. Arquitectura de Componentes (Usa Tablas)
4. ## 3. Lógica Central y Validaciones
5. ## 4. Manejo de Errores y Excepciones (Usa Tablas)
6. ## 5. Guía de Integración / Uso
"""
    },
    "pdf": {
        "role": "Ingeniero de Software Senior",
        "objective": "Informe Técnico Formal para exportación a PDF",
        "format_instructions": """
- NO uses tablas de Markdown (ej. |---|). Usa listas con guiones para describir variables.
- NO uses negritas con asteriscos (ej. **texto**). Escribe el texto limpio.
- Para los títulos de sección, usa ÚNICAMENTE el prefijo '## ' seguido del nombre.
- Los bloques de código deben ir entre triple comilla inversa ``` solo al inicio y al final.
- NO uses caracteres especiales como emojis o símbolos complejos fuera de Latin-1.
- Explica la lógica paso a paso de forma profesional.
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

ES_REFERENCE_TEMPLATE = """
### [X]. Análisis de Componentes (Ejemplo de Referencia)
| Módulo/Clase | Responsabilidad | Funciones Clave / Lógica |
| :--- | :--- | :--- |
| [Nombre] | [Función principal del componente] | [Método clave o flujo de lógica] |

### [X]. Matriz de API y Errores (Ejemplo de Referencia)
| Estado | Constante de Error | Razón/Condición |
| :--- | :--- | :--- |
| [400/500] | [NOMBRE_CODIGO_ERROR] | [Descripción de qué dispara este error] |
"""

ES_CHUNK_PROMPT = """
MODO FRAGMENTO ACTIVO:
1. PROHIBIDO: No generes títulos de nivel 1 (#), introducciones, alcances ni índices.
2. ENFOQUE: Comienza directamente con el análisis técnico de los archivos proporcionados.
3. JERARQUÍA: Usa títulos de nivel ### para cada componente o archivo analizado.
4. CONTINUIDAD: Redacta el contenido como si fuera un capítulo intermedio de un libro técnico.
5. SÍNTESIS: Si hay lógica repetida entre archivos del mismo fragmento, agrúpalos en una sola explicación.
"""
