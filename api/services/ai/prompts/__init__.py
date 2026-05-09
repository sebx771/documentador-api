from .es import (
    ES_CONFIGS,
    ES_REFERENCE_TEMPLATE,
    ES_CHUNK_PROMPT,
    ES_STRUCTURE_CHUNK,
    ES_CONSOLIDATION_PROMPT,
)
from .en import (
    EN_CONFIGS,
    EN_REFERENCE_TEMPLATE,
    EN_CHUNK_PROMPT,
    EN_STRUCTURE_CHUNK,
    EN_CONSOLIDATION_PROMPT,
)


def get_prompts(lang="es"):
    """
    Retorna el set de prompts configurado para el idioma solicitado.
    """
    if lang == "en":
        return {
            "configs": EN_CONFIGS,
            "reference": EN_REFERENCE_TEMPLATE,
            "chunk": EN_CHUNK_PROMPT,
            "chunk_structure": EN_STRUCTURE_CHUNK,
            "consolidation": EN_CONSOLIDATION_PROMPT,
            "edit_role": "You are a precise and conservative technical editor.",
            "edit_system": "You are an expert technical editor.",
            "edit_instruction": "Your task is to apply a user request to an EXISTING document.",
            "final_title": "# Project Documentation",
        }

    # Default: Español
    return {
        "configs": ES_CONFIGS,
        "reference": ES_REFERENCE_TEMPLATE,
        "chunk": ES_CHUNK_PROMPT,
        "chunk_structure": ES_STRUCTURE_CHUNK,
        "consolidation": ES_CONSOLIDATION_PROMPT,
        "edit_role": "Eres un editor técnico preciso y conservador.",
        "edit_system": "Eres un editor técnico experto.",
        "edit_instruction": "Tu tarea es aplicar una solicitud del usuario a un documento YA EXISTENTE.",
        "final_title": "# Documentación del Proyecto",
    }


# Exportamos palabras clave para detección de lenguaje
DANGEROUS_WORDS = {
    "es": [
        "indice",
        "índice",
        "introduccion",
        "introducción",
        "conclusion",
        "conclusión",
        "resumen",
        "estructura completa",
        "tabla de contenido",
        "capitulo",
        "capítulo",
        "sección",
        "seccion",
        "glosario",
        "bibliografía",
        "referencias",
    ],
    "en": [
        "index",
        "table of contents",
        "introduction",
        "conclusion",
        "summary",
        "complete structure",
        "chapter",
        "section",
        "glossary",
        "bibliography",
        "references",
    ],
}
