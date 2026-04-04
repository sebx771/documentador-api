# EasyDocs API - Documentación Técnica

## 1. Definición y Alcance
EasyDocs API es una aplicación web diseñada para generar documentación técnica en formato PDF y Markdown. La API ofrece endpoints para descargar la documentación en diferentes formatos y maneja errores comunes como endpoints no encontrados y métodos HTTP no permitidos.


## 2. Arquitectura de Componentes
La arquitectura de EasyDocs API se compone de los siguientes componentes:
* `EasyDocsPDF`: una clase que hereda de `FPDF` y se encarga de convertir texto en Markdown a PDF.
* `app`: la aplicación Flask que maneja las rutas y los endpoints de la API.
* `download_routes` y `zip_routes`: blueprints que registran las rutas para descargar la documentación en diferentes formatos.

## 3. Lógica de Negocio y Validaciones
La lógica de negocio de EasyDocs API se centra en la generación de documentación técnica en diferentes formatos. Las validaciones incluyen:
* Verificación de la longitud del código: se verifica que el código tenga una longitud entre `MIN_CODE_LENGTH` (10) y `MAX_CODE_LENGTH` (50000).
* Manejo de errores: se manejan errores comunes como endpoints no encontrados y métodos HTTP no permitidos.

Algunas reglas de negocio importantes son:
* La API solo admite solicitudes GET y POST.
* La API solo admite la generación de documentación en formato PDF y Markdown.
* La API maneja errores comunes como endpoints no encontrados y métodos HTTP no permitidos.

## 4. Guía de Integración
Para integrar EasyDocs API en una aplicación, se puede utilizar el siguiente ejemplo de uso con JSON:
```json
{
  "mensaje": "¡Bienvenido a EasyDocs API!",
  "version": "1.1.0",
  "endpoints": [
    {
      "ruta": "/download/<file_type>",
      "metodo": "POST",
      "descripcion": "Genera documentación en el formato especificado (pdf o markdown)",
      "parametros": {
        "file_type": "Tipo de archivo: 'pdf' o 'markdown'"
      }
    }
  ]
}
```
Para generar documentación en formato PDF, se puede enviar una solicitud POST a `/download/pdf` con el código en Markdown en el cuerpo de la solicitud.

## 5. Configuración y Logging
La configuración de EasyDocs API se centra en la configuración de logging y la versión de la API. La configuración de logging se establece en el nivel de información y se utiliza el formato `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`. La versión de la API se establece en `1.1.0`.

## 6. Seguridad
La seguridad de EasyDocs API se centra en el manejo de errores comunes y la validación de la longitud del código. Sin embargo, es importante mencionar que la API no incluye medidas de seguridad adicionales como autenticación o autorización. Es importante considerar la implementación de estas medidas para proteger la API y sus datos.

---

# Módulo: Descarga de Documentación

## 1. Definición y Alcance
El módulo de descarga de documentación es un componente de la aplicación que permite a los usuarios descargar documentación técnica en diferentes formatos (PDF y Markdown) para un código fuente proporcionado. El módulo utiliza una inteligencia artificial (IA) para generar la documentación y cuenta con un sistema de caché para mejorar el rendimiento.

## 2. Arquitectura de Componentes
El módulo de descarga de documentación se compone de los siguientes componentes:
* `DocumentadorIA`: un servicio que utiliza inteligencia artificial para generar documentación técnica a partir de un código fuente.
* `CacheService`: un servicio que almacena los resultados de la generación de documentación en un caché para evitar la regeneración de documentación para el mismo código fuente.
* `EasyDocsPDF`: una utilidad que permite generar archivos PDF a partir de contenido Markdown.
* `download_routes`: un conjunto de rutas de la aplicación que manejan las solicitudes de descarga de documentación.

## 3. Lógica de Negocio y Validaciones
La lógica de negocio del módulo de descarga de documentación se puede resumir en los siguientes pasos:
* Validar el tipo de archivo solicitado (PDF o Markdown).
* Obtener el código fuente del request.
* Validar el código fuente (longitud mínima y máxima).
* Buscar en el caché si ya se ha generado documentación para el mismo código fuente.
* Si no se encuentra en el caché, generar la documentación utilizando la inteligencia artificial.
* Almacenar el resultado en el caché.
* Generar el archivo solicitado (PDF o Markdown) a partir de la documentación generada.

Las validaciones realizadas en el módulo incluyen:
* Verificar que el tipo de archivo solicitado sea válido (PDF o Markdown).
* Verificar que el código fuente tenga una longitud mínima y máxima válida.
* Verificar que el request contenga un campo `codigo` si se proporciona como JSON.

## 4. Guía de Integración
Para utilizar el módulo de descarga de documentación, se puede realizar una solicitud POST a la ruta `/download/<file_type>` con el código fuente en el cuerpo del request. El tipo de archivo solicitada se especifica en la ruta (PDF o Markdown).

Ejemplo de uso con JSON:
```json
{
  "codigo": "def suma(a, b): return a + b"
}
```

## 5. Consideraciones de Rendimiento
El módulo de descarga de documentación utiliza un sistema de caché para mejorar el rendimiento. El caché almacena los resultados de la generación de documentación para el mismo código fuente, lo que evita la regeneración de documentación para el mismo código.

## 6. Errores y Excepciones
El módulo de descarga de documentación maneja los siguientes errores y excepciones:
* `INVALID_FILE_TYPE`: el tipo de archivo solicitado no es válido (PDF o Markdown).
* `INVALID_CONTENT_TYPE`: el request no contiene un campo `codigo` si se proporciona como JSON.
* `MISSING_FIELD`: el campo `codigo` es requerido pero no se proporciona.
* `INTERNAL_SERVER_ERROR`: error interno del servidor al generar documentación.

---

# Módulo: Documentador API

## 1. Definición y Alcance
El módulo "Documentador API" es un conjunto de rutas y servicios diseñados para generar documentación técnica en formato Markdown y PDF a partir de código fuente proporcionado. El alcance de este módulo incluye la validación del código fuente, la generación de documentación utilizando inteligencia artificial y la descarga de los documentos generados.

## 2. Arquitectura de Componentes
La arquitectura de componentes del módulo "Documentador API" se compone de los siguientes elementos:
- **Rutas**: Se definen dos rutas principales, `/descargar-md` y `/descargar-pdf`, para la generación y descarga de documentación en formato Markdown y PDF, respectivamente.
- **Servicios**: El módulo utiliza servicios de inteligencia artificial (`DocumentadorIA`) para generar la documentación a partir del código fuente.
- **Utilidades**: Se utilizan varias utilidades (`base`, `validate`, `bytes_utils`) para la decodificación de datos, validación del código fuente y preparación de la descarga de archivos.

## 3. Lógica de Negocio y Validaciones
La lógica de negocio y las validaciones del módulo "Documentador API" se pueden resumir en los siguientes puntos:
- **Validación de contenido**: Se verifica que el request contenga un JSON válido con el campo `codigo` obligatorio.
- **Decodificación del código**: El código fuente se decodifica desde base64 a string.
- **Validación del código fuente**: Se verifica que el código fuente tenga una longitud válida (entre `MIN_CODE_LENGTH` y `MAX_CODE_LENGTH`).
- **Generación de documentación**: La documentación se genera utilizando la inteligencia artificial (`DocumentadorIA`) a partir del código fuente validado.
- **Preparación de la descarga**: Los documentos generados se preparan para su descarga en formato Markdown o PDF.

## 4. Guía de Integración
Para integrar el módulo "Documentador API" en una aplicación, se deben seguir los siguientes pasos:
- **Enviar un request POST** a la ruta `/descargar-md` o `/descargar-pdf` con un JSON que contenga el campo `codigo` con el código fuente codificado en base64.
- **Recibir el documento generado**: El servidor responderá con el documento generado en formato Markdown o PDF, listo para ser descargado.

### Ejemplo de Uso con JSON
```json
{
  "codigo": "SGVsbG8gd29ybGQh"
}
```
Donde `"SGVsbG8gd29ybGQh"` es el código fuente codificado en base64.

## 5. Manejo de Errores
El módulo "Documentador API" maneja los siguientes errores:
- **Error de contenido**: Si el request no contiene un JSON válido o falta el campo `codigo`, se devuelve un error con código `400` y mensaje de error correspondiente.
- **Error de validación**: Si el código fuente no cumple con las validaciones (longitud inválida), se devuelve un error con código `400` y mensaje de error correspondiente.
- **Error interno**: Si ocurre un error inesperado durante la generación de la documentación, se devuelve un error con código `500` y mensaje de error correspondiente.

---

# Módulo: Zip

## 1. Definición y Alcance
El módulo "Zip" es un componente de la API que se encarga de procesar archivos ZIP y generar documentación automática. El alcance de este módulo incluye la recepción de archivos ZIP, la validación de su contenido, la generación de documentación en diferentes formatos y la devolución de metadatos sobre el procesamiento.

## 2. Arquitectura de Componentes
El módulo "Zip" se compone de los siguientes componentes:
| Componente | Descripción |
| --- | --- |
| `ZipService` | Servicio responsable de la manipulación de archivos ZIP |
| `DocumentationOrchestrator` | Servicio que orquesta la generación de documentación |
| `ChunkingService` | Servicio que se encarga de dividir el contenido del archivo ZIP en chunks |
| `CacheService` | Servicio que proporciona una caché para almacenar resultados intermedios |

## 3. Lógica de Negocio y Validaciones
El módulo "Zip" sigue las siguientes reglas de negocio:
* Se permite solo archivos ZIP
* El tamaño máximo del archivo ZIP es de 10MB
* Se permite especificar el tipo de documento de salida (markdown, pdf, word)
* Se permite especificar requisitos adicionales para la documentación
* Se valida el contenido del archivo ZIP y se devuelve un error si es inválido
* Se devuelve un error si el archivo ZIP es demasiado grande o vacío

## 4. Guía de Integración
Para integrar el módulo "Zip" en una aplicación, se debe realizar una solicitud POST al endpoint `/upload-zip` con el archivo ZIP y los parámetros adicionales (tipo de documento y requisitos adicionales).

Ejemplo de solicitud:
```json
{
  "file": "archivo.zip",
  "doc_type": "markdown",
  "extra_requirements": "requisitos adicionales"
}
```

## 5. Consideraciones de Rendimiento
El módulo "Zip" utiliza una caché para almacenar resultados intermedios y mejorar el rendimiento. La caché se configura con un tamaño máximo de 100 elementos y un tiempo de vida de 1 hora. El módulo también utiliza un servicio de chunking para dividir el contenido del archivo ZIP en chunks y procesarlos de manera paralela.

---

# Módulo: DocumentadorIA

## 1. Definición y Alcance
El módulo `DocumentadorIA` es un servicio diseñado para generar documentación técnica detallada para informes basados en código fuente proporcionado. Utiliza la API de Groq para procesar el código y generar la documentación en diferentes formatos, como Markdown, PDF y Word.

## 2. Arquitectura de Componentes
A continuación, se presenta la tabla de diccionario de datos para el m��dulo `DocumentadorIA`:

| Campo | Tipo | Propósito |
| --- | --- | --- |
| `api_key` | string | Clave de API para autenticación con Groq |
| `client` | objeto | Instancia del cliente Groq |
| `model` | string | Modelo de lenguaje utilizado para la generación de documentación |
| `tipo` | string | Tipo de documento a generar (Markdown, PDF o Word) |
| `codigo_fuente` | string | Código fuente a analizar para generar la documentación |
| `extra` | string | Requisito adicional del usuario para la generación de documentación |

## 3. Lógica de Negocio y Validaciones
A continuación, se presentan las reglas de negocio y validaciones implementadas en el módulo `DocumentadorIA`:

* La clave de API (`api_key`) debe estar configurada en las variables de entorno.
* El tipo de documento (`tipo`) debe ser uno de los siguientes: Markdown, PDF o Word.
* El código fuente (`codigo_fuente`) debe ser proporcionado para generar la documentación.
* El requisito adicional del usuario (`extra`) es opcional.
* La generación de documentación se realiza mediante la API de Groq, utilizando el modelo de lenguaje especificado (`model`).

## 4. Guía de Integración
A continuación, se presenta un ejemplo de cómo utilizar el módulo `DocumentadorIA` para generar documentación técnica en formato Markdown:
```json
{
  "codigo_fuente": "import os\nfrom groq import Groq\nfrom dotenv import load_dotenv",
  "tipo": "markdown",
  "extra": "Requisito adicional del usuario"
}
```

## 5. Errores y Excepciones
El módulo `DocumentadorIA` maneja los siguientes errores y excepciones:

* `ValueError`: si la clave de API no está configurada o si el tipo de documento no es soportado.
* `Exception`: si ocurre un error al llamar a la API de Groq o al generar la documentación.

---

# Módulo: Cache y Chunking

## 1. Definición y Alcance
El módulo "Cache y Chunking" se encarga de proporcionar servicios de caché y chunking para optimizar el rendimiento y la escalabilidad de la aplicación. El servicio de caché utiliza Redis para almacenar y recuperar datos, mientras que el servicio de chunking divide grandes cantidades de datos en chunks manejables para su procesamiento.

## 2. Arquitectura de Componentes
La arquitectura del módulo "Cache y Chunking" se compone de dos servicios principales:
* `CacheService`: se encarga de interactuar con Redis para almacenar y recuperar datos.
* `ChunkingService`: se encarga de dividir grandes cantidades de datos en chunks manejables.

### Tabla de Diccionario de Datos
| Campo | Descripción | Tipo |
| --- | --- | --- |
| `max_size` | Tamaño máximo de la caché | `int` |
| `ttl_seconds` | Tiempo de vida de los datos en la caché | `int` |
| `enable_lru` | Indica si se debe utilizar el algoritmo LRU | `bool` |
| `max_chunk_size` | Tamaño máximo de cada chunk | `int` |
| `max_files_per_chunk` | Número máximo de archivos por chunk | `int` |
| `max_tokens_estimate` | Estimación máxima de tokens por chunk | `int` |

## 3. Lógica de Negocio y Validaciones
La lógica de negocio del módulo "Cache y Chunking" se centra en la gestión de la caché y el chunking de datos. Las validaciones se realizan en los siguientes puntos:
* `CacheService`:
  + Verifica si la caché está configurada correctamente.
  + Verifica si el dato a almacenar o recuperar es válido.
* `ChunkingService`:
  + Verifica si la lista de archivos es válida.
  + Verifica si el tamaño y la cantidad de archivos por chunk son válidos.

### Reglas de Negocio
* La caché se utiliza para almacenar y recuperar datos de manera eficiente.
* El chunking se utiliza para dividir grandes cantidades de datos en chunks manejables.
* Los datos se almacenan en la caché con un tiempo de vida determinado.
* Los chunks se crean según el tamaño y la cantidad de archivos.

## 4. Guía de Integración
Para integrar el módulo "Cache y Chunking" en la aplicación, se deben seguir los siguientes pasos:
1. Importar el módulo `CacheService` y `ChunkingService`.
2. Configurar la caché y el chunking según las necesidades de la aplicación.
3. Utilizar los métodos `get`, `set` y `clear` de `CacheService` para interactuar con la caché.
4. Utilizar el método `create_chunks` de `ChunkingService` para dividir grandes cantidades de datos en chunks manejables.

---

# API de Documentador - Utilidades

## 1. Definición y Alcance
El módulo "API de Documentador" es un conjunto de utilidades y validaciones diseñadas para manejar solicitudes y respuestas en una aplicación web. Su alcance incluye la extracción de datos de solicitudes, la validación de código fuente y la configuración de rutas para la aplicación.

## 2. Arquitectura de Componentes
A continuación, se describe la arquitectura de componentes del módulo:

* `get_request.py`: Utilidad para extraer datos de solicitudes HTTP.
* `validate.py`: Utilidad para validar código fuente recibido en solicitudes.
* `vercel.json`: Configuración de rutas y builds para la aplicación.

## 3. Lógica de Negocio y Validaciones
La lógica de negocio y validaciones se pueden resumir en los siguientes puntos:

* La función `get_request_data` extrae datos de solicitudes HTTP, ya sea de archivos o de JSON.
* La función `validar_codigo` valida el código fuente recibido en solicitudes, comprobando que no esté vacío y que su longitud esté dentro de los límites permitidos.
* Las reglas de negocio para la validación de código fuente son:
  + El código no puede estar vacío.
  + El código debe tener al menos `MIN_CODE_LENGTH` caracteres.
  + El código no puede exceder `MAX_CODE_LENGTH` caracteres.

## 4. Configuración de Rutas
La configuración de rutas se define en el archivo `vercel.json`. A continuación, se describe la configuración:
* La ruta `/` se redirige a `api/main.py`.
* El build se realiza en `api/main.py` utilizando `@vercel/python`.

## 5. Consideraciones de Seguridad
Es importante tener en cuenta las siguientes consideraciones de seguridad:
* La validación de código fuente es crucial para prevenir ataques de inyección de código.
* La configuración de rutas y builds debe ser revisada regularmente para asegurarse de que no haya vulnerabilidades de seguridad.