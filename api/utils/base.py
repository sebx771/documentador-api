import base64


def base64_to_string(b64):

    try:
        bytes_data = b64.encode('utf-8')
        decoded_bytes = base64.b64decode(bytes_data)
        return decoded_bytes.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Error al decodificar base64: {str(e)}")