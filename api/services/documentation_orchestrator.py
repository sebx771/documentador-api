"""
Fachada de compatibilidad — conservada para evitar romper importaciones existentes.

Toda la lógica ha sido trasladada a :mod:`api.services.orchestrator`.
Para nuevo código, importar directamente desde allí; este módulo se mantendrá
como punto de entrada compatible.
"""

# Reexporta la clase bajo su nombre original para que
#   from api.services.documentation_orchestrator import DocumentationOrchestrator
# continúe funcionando sin modificaciones.
from .orchestrator import DocumentationOrchestrator  # noqa: F401

__all__ = ["DocumentationOrchestrator"]
