# EasyDocs

## ¿ Que es EasyDocs ?
**easyDocs** es un asistente de ingeniería de software impulsado por **Inteligencia Artificial** (Llama 3.1 vía Groq) diseñado para automatizar la creación de documentación técnica. Transforma estructuras de datos y lógica de negocio compleja en informes detallados, profesionales y listos para entregar.

## Stack Tecnologico 

*Python 3.12+🐍*: El lenguaje base por su gran ecosistema en IA.
*Groq Cloud API*: La plataforma que nos da la velocidad extrema usando el modelo Llama 3.1.
*FPDF / Python-docx*: Librerías encargadas de la exportación a formatos PDF y Word

## Funciones Planeadas Para EasyDocs

### Generación de Informes 
**Crea descripciones técnicas detalladas con lenguaje profesional** 

### Analisis Automatico de Estructuras de datos
**multiformato**
- markdown
- pdf
- word

## Despliegue (Vercel Serverless)
El proyecto está diseñado para ejecutarse en la infraestructura de Vercel utilizando Serverless Functions para optimizar el rendimiento y los costos.

*Runtime: Python 3.12.*

*Arquitectura*: Cada petición de generación de documentos es manejada por una función independiente, lo que garantiza rapidez y disponibilidad.

*Seguridad*: Las llaves de API se gestionan mediante variables de entorno en el panel de Vercel.


