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
Propósito, usuarios y capacidades principales del sistema, basados estrictamente en las fuentes.

## 2. Arquitectura de Componentes
Describe frontend, backend, persistencia e integraciones y cómo se relacionan. Incluye una tabla breve de componentes principales.

## 3. Lógica Central y Reglas de Negocio
Explica los flujos completos de negocio conectando rutas, middleware, controladores y servicios.

## 4. Modelo de Datos
Resume las entidades, relaciones y restricciones que consten en los modelos o el esquema.

## 5. API y Permisos
Documenta método, ruta, propósito y autenticación/autorización para cada endpoint verificado.

## 6. Configuración y Ejecución (Condicional)
Incluye requisitos, comandos y variables solo cuando estén presentes en las fuentes. Indica inconsistencias entre instrucciones y código.

## 7. Referencia por Archivo (Opcional)
Incluye únicamente detalles importantes que no estén explicados en las secciones anteriores; evita repetir un resumen para cada archivo.
"""

ES_CONSOLIDATION_PROMPT = """
Actúa como arquitecto de software y editor técnico senior. Transforma los análisis de fragmentos en una guía del sistema coherente; no entregues una colección de resúmenes archivo por archivo.

REGLAS DE ORO:
1. **Factualidad**: usa únicamente hechos presentes en la documentación recibida; no inventes rutas, contratos, variables, estados HTTP ni comportamientos.
2. **Síntesis**: deduplica conceptos y explica relaciones y flujos entre componentes. No uses un encabezado por cada archivo.
3. **Prioridad**: resume primero propósito, arquitectura, reglas de negocio, modelo de datos y API/permisos. Conserva detalles por archivo solo si aportan información que no aparezca en la síntesis.
4. **Trazabilidad**: menciona rutas de archivo junto a afirmaciones técnicas relevantes cuando estén disponibles.
5. **Incertidumbre**: si las fuentes se contradicen o falta información, indícalo explícitamente en vez de resolverlo por suposición.
6. **Formato**: sigue la estructura objetivo incluida en el mensaje. Omite las secciones condicionales cuando no haya evidencia. Responde únicamente en español.

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
