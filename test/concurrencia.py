import requests
import time
from concurrent.futures import ThreadPoolExecutor

def send():
    with open("ejercicios_javascript.zip", "rb") as f:
        r = requests.post(
            "http://127.0.0.1:5000/api/preview-zip",
            files={"file": ("PaginaWebHTML-main.zip", f, "application/zip")}
        )
    return r.status_code

start = time.time()

with ThreadPoolExecutor(max_workers=20) as executor:
    results = list(executor.map(lambda _: send(), range(200)))

end = time.time()

print("Exitosos:", results.count(200))
print("Tiempo total:", end - start)
print("Promedio:", (end - start)/200)