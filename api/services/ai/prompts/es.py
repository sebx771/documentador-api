# Configuraciones de prompts en Español

ES_STRUCTURE_CHUNK = """
### [Nombre del Módulo/Archivo]
- **Descripción**: Breve resumen técnico.
- **Componentes**: Lista de clases o funciones clave (usa tablas solo si es muy complejo).
- **Lógica y Validaciones**: Puntos clave de la implementación.
- **Errores**: Resumen de excepciones o códigos de error detectados.
"""

ES_STRUCTURE_FINAL = """
# [Título del Proyecto o Sistema]

## 1. Resumen Ejecutivo (Overview)
Breve descripción del propósito global del sistema.

## 2. Arquitectura de Componentes
Tabla consolidada de todos los módulos, su responsabilidad y funciones clave.

## 3. Lógica Central y Reglas de Negocio
Explicación detallada de los flujos principales y validaciones.

## 4. Matriz de Errores y Excepciones
Tabla consolidada de códigos de error, estados HTTP y condiciones.

## 5. Guía de Integración / Uso
Ejemplos de endpoints, parámetros y configuración necesaria.
"""

ES_CONSOLIDATION_PROMPT = """
Actúa como un Editor Técnico Senior. Tu tarea es CONSOLIDAR múltiples fragmentos de documentación en un único documento profesional y coherente.

REGLAS DE ORO:
1. **Deduplicación**: Si varios fragmentos mencionan el mismo componente o error, únelos en una sola entrada.
2. **Tablas Maestras**: Fusiona todas las tablas de "Componentes y Servicios" en una SOLA tabla maestra en la sección de Arquitectura.
3. **Matriz de Errores**: Fusiona todos los códigos de error en una SOLA tabla coherente.
4. **Fluidez**: Redacta transiciones entre secciones para que no parezca una lista de fragmentos pegados.
5. **Formato**: Sigue estrictamente la estructura de nivel 1 (#) y nivel 2 (##) definida en STRUCTURE_FINAL.
6. **Idioma**: Responde ÚNICAMENTE en Español.

DOCUMENTO A CONSOLIDAR:
"""

ES_CONFIGS = {
    "markdown": {
        "role": "Ingeniero de Software Senior",
        "objective": "Análisis técnico de un módulo de código para integración en un reporte mayor",
        "format_instructions": """
- Usa Markdown con títulos ## y ###
- Encierra variables y funciones en `código embebido` (IMPORTANTE)
- Adapta el nivel de detalle según la complejidad del código
- Usa un lenguaje técnico pero natural, evitando sonar robótico.
""",
        "structure": ES_STRUCTURE_FINAL,  # Default
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
2. ENFOQUE: Genera el análisis técnico siguiendo la estructura CHUNK_STRUCTURE.
3. CONTINUIDAD: Redacta para que sea fácil de consolidar luego.
"""
