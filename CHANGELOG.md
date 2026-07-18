# 📋 Changelog

Todos los cambios notables en EasyDocs se documenta en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
y este proyecto sigue [Semantic Versioning](https://semver.org/spec/v2.0.0.html).



## [2.4.1] - 2026/07/18

### fixed
- reemplazo de modelos deprecados del proveedor *groq* 
 - Llama 4 Scout 17B -> llama-3.1-8b-instant 
 - qwen 3 32B -> qwen 3 27B

## [2.4.0] - 2026/07/08

## changed 
- se modifica el chunking para que pueda dividir chunks que sea demasiados grandes
- se agrega back off a la llamada de los modelos

## [2.3.2] - 2026/05/9

### fixed
- remueve variable certificado ssl none para evitar ataques *man in the middle attack*

## changed
- mueve logica de negocio de *routes* a *controllers*

## [2.3.1] - 2026/05/1

### 🐛 fixed
- arregla generacion pdf de la ruta */api/upload-zip*

### changed
- remueve keys del diccionario de prompts innecesarias 


## [2.3.0] - 2026-04-22

### ✨ Added
- **Documentación Mejorada**
  - ARCHITECTURE.md con diagrama detallado de componentes
  - routing de modelos AI (fallback,chuncking)



- **Configuración Mejorada**
  - Soporte multiidioma (ES/EN) en prompts
  - .gitignore completo y robusto
  - .env.example detallado con comentarios
  - LICENSE MIT
  - Soporte para múltiples plataformas (Windows, macOS, Linux)

### 🐛 Fixed
- Manejo mejorado de errores en servicios
- Validación más estricta de inputs
- Mejor logging para debugging

### 📝 Docs
- Actualizado README con secciones de uso, API y deployment
- Documentación de variables de entorno
- Guías de desarrollo para colaboradores

---

## [2.2.0] - 2026-04-15

### ✨ Added

- Rate limiting con Redis
- Caché inteligente por hash
- Procesamiento de ZIPs completos

### 🐛 Fixed
- Manejo de caracteres especiales en nombres de archivo
- Detección de idioma mejorada

### Changed
- generacion de pdf desde *markdown-pdf*
- generacion de word desde *markdown-it*

---

## [2.1.0] - 2026-04-08

### ✨ Added
- Exportación a Word con python-docx
- Chunking automático de código grande


### 📝 Docs
- Documentación técnica inicial (doc_es.md, doc_en.md)



---

## [2.0.0] - 2026-04-01

### ✨ Added

- Generacion de documentacion desde .zip y archivos e.g *.py , .js , .go , .java*
- Generacion de PDF con FPDF


### 🏗️ Changed
- Reescritura completa con arquitectura modular
- API REST con Flask *recreacion de rutas*
- Generación de documentación desde JSON *(REMUEVE BASE64)* 

---

## [1.0.0] - 2026-03-01

### ✨ Added
- Prototipo inicial
- generacion desde JSON *(base64)*
- Integración con Groq API (Llama 3.1)
- Generación de documentación básica
- Exportación a Markdown
