from datetime import datetime
import requests

URL = "http://127.0.0.1:5000/api/download/pdf"  # ajusta a tu endpoint

def enviar_archivo(ruta_archivo, tipo="markdown", extra=None):
    with open(ruta_archivo, "rb") as f:
        files = {
            "file": (ruta_archivo, f, "text/plain")
        }

        data = {
            "tipo": tipo
        }

        if extra:
            data["extra"] = extra

        response = requests.post(URL, files=files, data=data)
       
        print("Status:", response.status_code)
        print("Respuesta:\n", response.text)
        return response.content

if __name__ == "__main__":
   for i in range(5):
    file= enviar_archivo("config.py", "markdown", "habla de las dependencias y su posible función en el proyecto")
  
   with open(f"documentacion{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf", "wb") as f:
        f.write(file)
