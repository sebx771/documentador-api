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
