"""
Capa de consolidación: agrupación por lotes, síntesis multirronda y validación de secciones.

Toma la documentación generada por cada fragmento y la fusiona
en un único documento coherente mediante rondas iterativas de consolidación con IA.
"""

from __future__ import annotations

import logging
import unicodedata
from typing import List, Optional

from .models import ChunkDocumentation

logger = logging.getLogger(__name__)

# Constantes de presupuesto por defecto; pueden ser modificadas por el orquestador.
DEFAULT_MAX_INPUT_TOKENS = 18_000
DEFAULT_MAX_ROUNDS = 8


def consolidate_chunks(
    chunk_results: List[ChunkDocumentation],
    extra_requirements: Optional[str],
    language: str,
    documentador,
    max_input_tokens: int = DEFAULT_MAX_INPUT_TOKENS,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
) -> str:
    """Fusiona *chunk_results* en un único documento de documentación.

    Args:
        chunk_results: Resultados exitosos de los fragmentos (no se esperan
            elementos con ``error=True`` aquí; el pipeline invoca
            :func:`generation.raise_for_failed_chunks` antes de esta etapa).
        extra_requirements: Directivas opcionales aplicadas tras la consolidación
            mediante :meth:`documentador.apply_extra`.
        language: Código ISO de idioma enviado a las llamadas de IA y para la validación de encabezados.
        documentador: Backend de IA que expone ``consolidate``, ``apply_extra`` y
            ``estimate_input_tokens``.
        max_input_tokens: Presupuesto de tokens por grupo de consolidación.
        max_rounds: Límite estricto de rondas de consolidación para evitar bucles infinitos.

    Returns:
        La cadena de texto con la documentación final consolidada.

    Raises:
        RuntimeError: Cuando no hay fragmentos, todos producen textos vacíos, el modelo
            devuelve una consolidación vacía, la convergencia se detiene sin progreso,
            se supera el límite de rondas o faltan secciones requeridas en el documento final.
    """
    if not chunk_results:
        raise RuntimeError("No se generaron fragmentos para consolidar.")

    documents = [
        (r.documentation or "").strip()
        for r in chunk_results
        if (r.documentation or "").strip()
    ]
    if not documents:
        raise RuntimeError("Los fragmentos no contienen documentación utilizable.")

    final_doc = _consolidate_in_batches(
        documents, language, documentador, max_input_tokens, max_rounds
    )

    if extra_requirements and extra_requirements.strip():
        final_doc = documentador.apply_extra(
            final_doc, extra_requirements, lang=language
        )

    validate_sections(final_doc, language)
    return final_doc


# ---------------------------------------------------------------------------
# Funciones auxiliares internas
# ---------------------------------------------------------------------------


def _consolidate_in_batches(
    documents: List[str],
    language: str,
    documentador,
    max_input_tokens: int,
    max_rounds: int,
) -> str:
    current_documents = documents

    for round_number in range(1, max_rounds + 1):
        groups = _group_documents(current_documents, documentador, max_input_tokens)
        logger.info(
            "Consolidación IA: ronda %d, %d documentos en %d grupos",
            round_number,
            len(current_documents),
            len(groups),
        )

        consolidated = [
            documentador.consolidate(group, lang=language) for group in groups
        ]

        if any(not result or not result.strip() for result in consolidated):
            raise RuntimeError("El modelo devolvió una consolidación vacía.")

        if len(groups) == 1:
            logger.info("Consolidación IA completada en la ronda %d", round_number)
            return consolidated[0].strip()

        current_size = sum(
            _estimate_tokens(doc, documentador) for doc in current_documents
        )
        consolidated_size = sum(
            _estimate_tokens(doc, documentador) for doc in consolidated
        )
        next_group_count = len(
            _group_documents(consolidated, documentador, max_input_tokens)
        )

        if consolidated_size >= current_size and next_group_count >= len(groups):
            raise RuntimeError(
                "La consolidación por grupos no redujo el volumen estimado; "
                "se detuvo para evitar una iteración sin progreso."
            )

        current_documents = consolidated

    raise RuntimeError(
        f"La consolidación superó el máximo de {max_rounds} rondas."
    )


def _group_documents(
    documents: List[str],
    documentador,
    max_input_tokens: int,
) -> List[str]:
    """Empaqueta *documents* en grupos que quepan dentro del presupuesto *max_input_tokens*."""
    groups: List[str] = []
    current_group = ""

    for document in documents:
        for part in _split_to_budget(document, documentador, max_input_tokens):
            candidate = f"{current_group}\n\n{part}".strip()
            if (
                current_group
                and _estimate_tokens(candidate, documentador) > max_input_tokens
            ):
                groups.append(current_group)
                current_group = part
            else:
                current_group = candidate

    if current_group:
        groups.append(current_group)

    return groups


def _split_to_budget(
    document: str,
    documentador,
    max_input_tokens: int,
) -> List[str]:
    """Divide un *document* en partes que quepan individualmente dentro del presupuesto de tokens."""
    if _estimate_tokens(document, documentador) <= max_input_tokens:
        return [document]

    max_chars = max_input_tokens * 3
    remaining = document
    parts: List[str] = []

    while remaining:
        if _estimate_tokens(remaining, documentador) <= max_input_tokens:
            parts.append(remaining.strip())
            break

        boundary = remaining.rfind("\n\n", 0, max_chars)
        if boundary <= 0:
            boundary = remaining.rfind("\n", 0, max_chars)
        if boundary <= 0:
            boundary = max_chars

        parts.append(remaining[:boundary].strip())
        remaining = remaining[boundary:].strip()

    return [p for p in parts if p]


def _estimate_tokens(document: str, documentador) -> int:
    return documentador.estimate_input_tokens("", document)


def validate_sections(documentation: str, language: str) -> None:
    """Lanza :class:`RuntimeError` si faltan secciones principales requeridas en el documento.

    La comprobación de secciones no distingue entre mayúsculas/minúsculas ni acentos,
    evitando falsos negativos ante pequeñas variaciones en los encabezados.
    """
    if not documentation or not documentation.strip():
        raise RuntimeError("La documentación final está vacía.")

    required = (
        ("resumen ejecutivo", "arquitectura de componentes", "lógica central")
        if language == "es"
        else ("executive summary", "component architecture", "core logic")
    )

    headings = [
        _normalize(line.lstrip("#").strip())
        for line in documentation.splitlines()
        if line.startswith("#")
    ]
    missing = [
        section
        for section in required
        if not any(_normalize(section) in heading for heading in headings)
    ]

    if missing:
        raise RuntimeError(
            "La consolidación no produjo las secciones requeridas: "
            + ", ".join(missing)
        )


def _normalize(text: str) -> str:
    return (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
