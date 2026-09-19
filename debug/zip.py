import requests
import time

url = "http://127.0.0.1:5000/api/upload-zip"

# archivo zip que vas a enviar
w = 3
for i in range(w):
  
  files = {
    "file": ("PaginaWebHTML-main.zip", open("PaginaWebHTML-main.zip", "rb"), "application/zip")
  }
  response = requests.post(url, files=files)

  print("Status:", response.status_code)
  if response.status_code == 200:
    print("OK - Descarga iniciada")
  else:
    print("Response:", response.text[:200] if response.text else "Empty")