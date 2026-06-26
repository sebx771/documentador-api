import io


def preparar_descarga(contenido):
    buf = io.BytesIO()
    if isinstance(contenido, str):
        contenido = contenido.encode("utf-8")
    buf.write(contenido)
    buf.seek(0)  # Volvemos al inicio del "archivo" virtual
    return buf
