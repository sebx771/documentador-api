import requests
import time

url = "http://127.0.0.1:5000/api/d"

# archivo zip que vas a enviar
w= 100
for i in  range(w):
 
  files = {
    "file": ("PaginaWebHTML-main.zip", open("PaginaWebHTML-main.zip", "rb"), "application/zip")
}
  response = requests.post(url, files=files)

  print("Status:", response.status_code)
  print("Response:", response.text)