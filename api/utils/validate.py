from typing import Tuple


def validar_codigo(
    codigo_fuente, logger, MIN_CODE_LENGTH, MAX_CODE_LENGTH
) -> Tuple[bool, dict]:
    """
    Valida el código fuente recibido en el request.
    Args:
        codigo_fuente: Código fuente a validar
        logger: Logger para registrar advertencias
        MIN_CODE_LENGTH: Longitud mínima permitida
        MAX_CODE_LENGTH: Longitud máxima permitida

    Returns:
        Tuple(bool, dict): (Es válido, Respuesta de error si no es válido)
    """
    # Validar que el código no esté vacío
    if not codigo_fuente or not codigo_fuente.strip():
        logger.warning("Código fuente vacio")
        return False, {
            "error": "El código fuente no puede estar vacio",
            "codigo_error": "EMPTY_CODE",
        }

    # Validar longitud mínima
    if len(codigo_fuente.strip()) < MIN_CODE_LENGTH:
        logger.warning(f"Código demasiado corto: {len(codigo_fuente)} caracteres")
        return False, {
            "error": f"El código debe tener al menos {MIN_CODE_LENGTH} caracteres",
            "codigo_error": "CODE_TOO_SHORT",
        }

    # Validar longitud máxima
    if len(codigo_fuente) > MAX_CODE_LENGTH:
        logger.warning(f"Código excede límite: {len(codigo_fuente)} caracteres")
        return False, {
            "error": f"El código excede el límite de {MAX_CODE_LENGTH} caracteres",
            "codigo_error": "CODE_TOO_LONG",
        }

    return True, None
