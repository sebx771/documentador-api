import zipfile
from ..export.docx_gen import EasyDocsDOCX
import io
import os
import time


class ZipService():
    def __init__(self):
        self.allowed_extensions = {".py", ".java", ".go", ".js", ".ts",".php",".css", ".html", ".json", ".xml", ".yml", ".yaml"}
        self.ignore_folders= {"node_modules",".git",".gitignore",".DS_Store","__pycache__",".venv"}
        self.ignore_files= {"package-lock.json", "yarn.lock"}

    def extraer_zip(self, contenido_bytes: bytes):
        MAX_FILES= 50
        codigo_total= []
        codigo_invalido= []
             
        try:
            with zipfile.ZipFile(io.BytesIO(contenido_bytes)) as zip_file:
                for file in zip_file.namelist():
                    _,ext= os.path.splitext(file.lower())

                    if file.endswith("/"):
                        continue

                    if any(folder in file for folder in self.ignore_folders):
                     continue

                    if any(file.endswith(ignore) for ignore in self.ignore_files):
                      continue

                    if ext in self.allowed_extensions:
                        try:
                            with zip_file.open(file) as f:
                                contenido= f.read().decode('utf-8',errors="ignore")
                                if contenido.strip():
                                 codigo_total.append(f"\n\n### Archivo:{file}\nLenguaje: {ext.replace('.', '')}\n\n{contenido}")

                                 if len(codigo_total) >= MAX_FILES:
                                    break 
                        except Exception as e:
                            codigo_invalido.append(f"Error al leer el archivo {file}: {str(e)}")
                            continue
        except zipfile.BadZipFile as e:
            print(f"Error al extraer el ZIP: {str(e)}")
            raise Exception("Archivo ZIP inválido o corrupto")
        
        return "\n".join(codigo_total) , codigo_invalido

    def crear_zip(self):
        pass

    def listar_contenido_zip(self, contenido_bytes:bytes)->list:
        resultado= []
        try:
            with zipfile.ZipFile(io.BytesIO(contenido_bytes)) as zip_file:
                for file in zip_file.namelist():
                    if file.endswith("/"):
                        continue

                    if any(folder in file for folder in self.ignore_folders):
                     continue

                    if any(file.endswith(ignore) for ignore in self.ignore_files):
                      continue
                    
                    _,ext= os.path.splitext(file.lower())
                    is_valid= ext in self.allowed_extensions
                    info= zip_file.getinfo(file)

                    f= {
                            "file":file,
                            "language":ext.replace(".",""),
                            "valid":is_valid,
                            "size": f"{round(info.file_size/1024,2)}kb"
                        }
                    resultado.append(f)
            
        except zipfile.BadZipFile as e:
         raise Exception("Archivo ZIP inválido o corrupto")
        
        return resultado
        
#test
if __name__ == "__main__":
    zip= ZipService()
    with open("ejercicios_javascript.zip", "rb") as f:
        contenido_bytes= f.read()
        codigo= zip.listar_contenido_zip(contenido_bytes)
        for c in codigo:
            time.sleep(2)
            print(c)
        
        