import asyncio
import httpx
from datetime import datetime

# Asegúrate de que este sea el endpoint que devuelve el PDF
URL = "http://127.0.0.1:5000/api/download/pdf" 

async def enviar_archivo(client, ruta_archivo, tipo="markdown", extra=None):
    try:
        # 1. LEER EL ARCHIVO PRIMERO
        # Esto evita que 5 tareas intenten mantener el archivo abierto al mismo tiempo
        with open(ruta_archivo, "rb") as f:
            contenido_binario = f.read()

        # 2. PREPARAR LOS DATOS
        files = {"file": (ruta_archivo, contenido_binario, "text/plain")}
        data = {"tipo": tipo}
        if extra:
            data["extra"] = extra

        # 3. PETICIÓN ASÍNCRONA
        # timeout=None es vital porque generar un PDF puede tardar más de 5 segundos
        response = await client.post(URL, files=files, data=data, timeout=None)
        
        if response.status_code == 200:
            print(f"✅ Recibido PDF de: {extra}")
            return response.content
        else:
            print(f"❌ Error {response.status_code} en {extra}: {response.text}")
            return None

    except Exception as e:
        print(f"🚨 Error inesperado: {e}")
        return None

async def main():
    async with httpx.AsyncClient() as client:
        tareas = []
        
        print("🚀 Iniciando peticiones en paralelo...")
        for i in range(5):
            # Agregamos la tarea a la lista
            msg_extra = f"Iteración {i+1}"
            tarea = enviar_archivo(client, "config.py", "markdown", msg_extra)
            tareas.append(tarea)

        # Ejecutamos las 5 al mismo tiempo
        resultados = await asyncio.gather(*tareas)

        # 4. GUARDAR LOS RESULTADOS
        for i, contenido_pdf in enumerate(resultados):
            if contenido_pdf:
                timestamp = datetime.now().strftime('%H%M%S')
                nombre_archivo = f"doc_{i+1}_{timestamp}.pdf"
                
                with open(nombre_archivo, "wb") as f:
                    f.write(contenido_pdf)
                print(f"💾 Archivo guardado: {nombre_archivo}")

if __name__ == "__main__":
    # Arrancamos el bucle de eventos
    asyncio.run(main())