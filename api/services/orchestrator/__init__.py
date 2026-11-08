"""
api.services.orchestrator
~~~~~~~~~~~~~~~~~~~~~~~~~

API pública del paquete del pipeline de documentación.

Importar :class:`DocumentationOrchestrator` desde aquí; *no* importar directamente
desde los submódulos internos, ya que su estructura interna puede evolucionar entre fases.
"""

from .pipeline import DocumentationOrchestrator

__all__ = ["DocumentationOrchestrator"]
