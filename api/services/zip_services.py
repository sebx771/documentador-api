import zipfile
from ..export.docx_gen import EasyDocsDOCX
import io
import os
import time
import logging

logger = logging.getLogger(__name__)


class ZipService:
    def __init__(self):
        self.allowed_extensions = {
            ".py",
            ".java",
            ".go",
            ".js",
            ".ts",
            ".php",
            ".css",
            ".html",
            ".json",
            ".xml",
            ".yml",
            ".yaml",
            ".kt"
        }
        self.ignore_folders = {
            "node_modules",
            ".git",
            ".gitignore",
            ".DS_Store",
            "__pycache__",
            ".venv",
            ".idea",
            ".vscode",
            "build",
            "gradle",
            ".gradle",
            "bin",
            "out",
            "target",
            "dist",
            "logs",
            "docs",
            "tests",
            "vendor",
            "composer.lock",
            "package-lock.json",
            "yarn.lock"
        }
        self.ignore_files = {"package-lock.json", "yarn.lock"}
        self.MAX_UNCOMPRESSED_SIZE = 40 * 1024 * 1024  # 40 MB máximo descomprimido
        self.MAX_FILES_COUNT = 300                      # Máximo 300 archivos en el ZIP

    def validar_zip_seguro(self, zip_file: zipfile.ZipFile) -> None:
        """
        Valida que el archivo ZIP no represente un riesgo de seguridad
        (ZIP Bomb, saturación de archivos o Path Traversal).
        """
        infolist = zip_file.infolist()

        if len(infolist) > self.MAX_FILES_COUNT:
            raise ValueError(
                f"El archivo ZIP contiene demasiados archivos ({len(infolist)}). "
                f"El máximo permitido es {self.MAX_FILES_COUNT}."
            )

        total_uncompressed = 0
        for info in infolist:
            filename = info.filename
            # Protección contra Path Traversal
            normalized = filename.replace("\\", "/")
            parts = normalized.split("/")
            if normalized.startswith("/") or ".." in parts:
                raise ValueError(
                    f"Ruta de archivo no permitida detectada en el ZIP: '{filename}'"
                )

            total_uncompressed += info.file_size
            if total_uncompressed > self.MAX_UNCOMPRESSED_SIZE:
                max_mb = self.MAX_UNCOMPRESSED_SIZE / (1024 * 1024)
                raise ValueError(
                    f"El tamaño total descomprimido excede el límite de seguridad permitido ({max_mb:.0f} MB)."
                )

    def extraer_zip(self, contenido_bytes: bytes):
        MAX_FILES = 50
        codigo_total = []
        codigo_invalido = []

        try:
            with zipfile.ZipFile(io.BytesIO(contenido_bytes)) as zip_file:
                self.validar_zip_seguro(zip_file)
                for file in zip_file.namelist():
                    _, ext = os.path.splitext(file.lower())

                    if file.endswith("/"):
                        continue

                    if any(folder in file for folder in self.ignore_folders):
                        continue

                    if any(file.endswith(ignore) for ignore in self.ignore_files):
                        continue

                    if ext in self.allowed_extensions:
                        try:
                            with zip_file.open(file) as f:
                                contenido = f.read().decode("utf-8", errors="ignore")
                                if contenido.strip():
                                    codigo_total.append(
                                        f"\n\n### Archivo:{file}\nLenguaje: {ext.replace('.', '')}\n\n{contenido}"
                                    )

                                    if len(codigo_total) >= MAX_FILES:
                                        break
                        except Exception as e:
                            codigo_invalido.append(
                                f"Error al leer el archivo {file}: {str(e)}"
                            )
                            continue
        except ValueError:
            raise
        except zipfile.BadZipFile as e:
            logger.error(f"Error al extraer el ZIP: {str(e)}")
            raise ValueError("Archivo ZIP inválido o corrupto")

        return "\n".join(codigo_total), codigo_invalido

    def crear_zip(self, files: dict) -> bytes:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for filename, content in files.items():
                zf.writestr(filename, content)
        return buffer.getvalue()

    def listar_contenido_zip(self, contenido_bytes: bytes) -> list:
        resultado = []
        try:
            with zipfile.ZipFile(io.BytesIO(contenido_bytes)) as zip_file:
                self.validar_zip_seguro(zip_file)
                for file in zip_file.namelist():
                    if file.endswith("/"):
                        continue

                    if any(folder in file for folder in self.ignore_folders):
                        continue

                    if any(file.endswith(ignore) for ignore in self.ignore_files):
                        continue

                    _, ext = os.path.splitext(file.lower())
                    is_valid = ext in self.allowed_extensions
                    info = zip_file.getinfo(file)

                    f = {
                        "file": file,
                        "language": ext.replace(".", ""),
                        "valid": is_valid,
                        "size": f"{round(info.file_size/1024,2)}kb",
                    }
                    resultado.append(f)

        except ValueError:
            raise
        except zipfile.BadZipFile as e:
            logger.error(f"Error al listar contenido del ZIP: {str(e)}")
            raise ValueError("Archivo ZIP inválido o corrupto")

        return resultado

