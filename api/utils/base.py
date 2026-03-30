import base64


def base64_to_string(b64):

    try:
        if isinstance(b64, str):
         bytes_data = b64.encode('utf-8')
        else:
            bytes_data = b64
            
        decoded_bytes = base64.b64decode(bytes_data)
        return decoded_bytes.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Error al decodificar base64: {str(e)}")