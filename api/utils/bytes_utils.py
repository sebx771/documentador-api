import io

def preparar_descarga(contenido):
    buf = io.BytesIO()
    buf.write(contenido.encode('utf-8'))
    buf.seek(0)  # Volvemos al inicio del "archivo" virtual
    return buf