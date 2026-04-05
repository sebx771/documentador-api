# Documentación Técnica de Módulo "Whatsapp-bot-main"
## 1. Definición y Alcance
El módulo "Whatsapp-bot-main" es un bot de WhatsApp diseñado para interactuar con usuarios a través de la plataforma de mensajería instantánea. El alcance de este módulo incluye la recepción y procesamiento de mensajes de texto, la verificación de webhooks y la respuesta a los usuarios con mensajes personalizados.

## 2. Arquitectura de Componentes
La arquitectura del módulo "Whatsapp-bot-main" se compone de los siguientes componentes:
* `app.js`: El archivo principal que inicia el servidor y configura las rutas.
* `config/env.js`: El archivo de configuración que maneja las variables de entorno.
* `controllers/webhookController.js`: El controlador que maneja las solicitudes entrantes y salientes del webhook.
* `routes/webhookRoutes.js`: Las rutas que envían y reciben información del controlador del webhook.
* `services/messageHandler.js`: El servicio que maneja los mensajes y responde a los usuarios.
* `services/whatsappService.js`: El servicio que interactúa con la API de WhatsApp para enviar y recibir mensajes.

## 3. Lógica de Negocio y Validaciones
La lógica de negocio del módulo "Whatsapp-bot-main" se basa en las siguientes reglas:
* Verificar la autenticidad del webhook mediante el token de verificación.
* Procesar los mensajes de texto y responder con mensajes personalizados.
* Enviar mensajes de bienvenida y menús interactivos a los usuarios.
* Marcar los mensajes como leídos después de procesarlos.

Las validaciones incluyen:
* Verificar la existencia de las variables de entorno necesarias.
* Verificar la autenticidad del token de verificación del webhook.
* Verificar la validez de los mensajes de texto recibidos.

## 4. Guía de Integración
Para integrar el módulo "Whatsapp-bot-main" con la API de WhatsApp, siga los siguientes pasos:
1. Configure las variables de entorno en el archivo `config/env.js`.
2. Inicie el servidor ejecutando el comando `npm start`.
3. Envíe un mensaje de texto al número de WhatsApp configurado para probar la funcionalidad del bot.

Ejemplo de uso con JSON:
```json
{
  "to": "1234567890",
  "body": "Hola, ¿cómo estás?",
  "type": "text"
}
```
Este mensaje se enviará al número de WhatsApp configurado y el bot responderá con un mensaje personalizado.

## 5. Configuración de Variables de Entorno
Las variables de entorno necesarias para el funcionamiento del módulo "Whatsapp-bot-main" son:
| Variable | Descripción |
| --- | --- |
| `WEBHOOK_VERIFY_TOKEN` | Token de verificación del webhook |
| `API_TOKEN` | Token de autenticación de la API de WhatsApp |
| `BUSINESS_PHONE` | Número de teléfono de la empresa |
| `API_VERSION` | Versión de la API de WhatsApp |
| `PORT` | Puerto del servidor |

Estas variables deben ser configuradas en el archivo `config/env.js` para que el módulo funcione correctamente.

## 6. Manejo de Errores
El módulo "Whatsapp-bot-main" maneja los errores de la siguiente manera:
* Los errores de autenticación del webhook se manejan mediante la verificación del token de verificación.
* Los errores de procesamiento de mensajes se manejan mediante la verificación de la validez de los mensajes de texto recibidos.
* Los errores de envío de mensajes se manejan mediante la captura de excepciones en el servicio `whatsappService.js`.

En caso de error, el módulo registra el error en la consola y continúa funcionando.