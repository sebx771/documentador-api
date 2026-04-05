## Chunk 1
Archivos: ejercicios_javascript/edades.js, ejercicios_javascript/ejer.js, ejercicios_javascript/emisora.js

# Documentación Técnica de Módulo "Ejercicios JavaScript"
## 1. Definición y Alcance
El módulo "Ejercicios JavaScript" se compone de tres archivos: `edades.js`, `ejer.js` y `emisora.js`. Cada archivo contiene un conjunto de funciones y lógica de negocio para resolver problemas específicos.

## 2. Arquitectura de Componentes
A continuación, se presenta una tabla con los componentes y sus respectivas descripciones:

| Componente | Descripción |
| --- | --- |
| `edades.js` | Registro de edades y cálculo de estadísticas |
| `ejer.js` | Calculadora de área y perímetro de figuras geométricas |
| `emisora.js` | Registro de personas y visualización de información |

## 3. Lógica de Negocio y Validaciones
A continuación, se presentan las reglas de negocio y validaciones para cada componente:

* `edades.js`:
 + Se solicita la edad de 10 personas y se valida que esté entre 1 y 120 años.
 + Se calculan estadísticas como el número de menores de edad, mayores de edad, adultos mayores, edad mínima, edad máxima y promedio de edades.
* `ejer.js`:
 + Se solicita la selección de una figura geométrica (triángulo, rectángulo, cuadrado o círculo) y la operación a realizar (área o perímetro).
 + Se solicitan los parámetros necesarios para calcular el área o perímetro de la figura seleccionada.
 + Se valida que los parámetros sean numéricos y estén dentro de los límites permitidos.
* `emisora.js`:
 + Se solicita la selección de una opción (agregar persona, mostrar información por posición o salir).
 + Se valida que la opción seleccionada sea válida.
 + Se solicitan los datos personales y se validan que sean correctos (nombre, cédula, fecha de nacimiento, correo electrónico, ciudad de residencia y ciudad de origen).
 + Se solicitan las canciones favoritas y se validan que sean correctas (título y artista).

## 4. Guía de Integración
A continuación, se presenta un ejemplo de uso de cada componente con JSON:

* `edades.js`:
```json
{
  "edades": [25, 30, 35, 20, 40, 45, 50, 55, 60, 65]
}
```
* `ejer.js`:
```json
{
  "figura": "triángulo",
  "operacion": "área",
  "base": 10,
  "altura": 20
}
```
* `emisora.js`:
```json
{
  "persona": {
    "nombre": "Juan",
    "cedula": "1234567890",
    "fechaNacimiento": "12/02/1990",
    "correo": "juan@example.com",
    "ciudadResidencia": "Ciudad de México",
    "ciudadOrigen": "Guadalajara",
    "canciones": [
      {
        "titulo": "Canción 1",
        "artista": "Artista 1"
      },
      {
        "titulo": "Canción 2",
        "artista": "Artista 2"
      }
    ]
  }
}
```
## 5. Consideraciones Adicionales
Es importante mencionar que los componentes `edades.js` y `ejer.js` utilizan la función `prompt` para solicitar input al usuario, mientras que el componente `emisora.js` utiliza un menú para seleccionar opciones. Además, los componentes `edades.js` y `ejer.js` realizan cálculos y validaciones en tiempo de ejecución, mientras que el componente `emisora.js` almacena y visualiza información en un objeto.

---

## Chunk 2
Archivos: ejercicios_javascript/numeros.js, ejercicios_javascript/package.json

# Documentación Técnica de Módulo "Numeros"
## 1. Definición y Alcance
El módulo "Numeros" es un programa escrito en JavaScript que se encarga de leer dos vectores de números enteros ordenados ascendentemente, combinarlos y ordenar el resultado. El programa utiliza la biblioteca `prompt-sync` para obtener la entrada del usuario de manera síncrona.

## 2. Arquitectura de Componentes
No hay una arquitectura de componentes compleja en este módulo, ya que se trata de un programa simple que realiza una tarea específica. Sin embargo, se pueden identificar los siguientes componentes:
- `leerVector`: función que se encarga de leer un vector de números enteros ordenados ascendentemente.
- `vector1` y `vector2`: variables que almacenan los vectores de números enteros leídos por el usuario.
- `combinado`: variable que almacena el vector combinado y ordenado.

## 3. Lógica de Negocio y Validaciones
La lógica de negocio del módulo "Numeros" se puede resumir en los siguientes puntos:
* Se le pide al usuario que ingrese 5 números enteros ordenados ascendentemente para cada vector.
* Se valida que cada número ingresado sea un número entero válido.
* Se valida que cada número ingresado sea mayor o igual al anterior en el mismo vector.
* Se combinan los dos vectores y se ordenan los números en orden ascendente.

Las reglas de negocio se pueden resumir en las siguientes:
* El usuario debe ingresar 5 números enteros para cada vector.
* Los números deben ser enteros válidos.
* Los números deben ser ordenados ascendentemente en cada vector.
* El vector combinado se ordena en orden ascendente.

## 4. Guía de Integración
Para integrar este módulo en otro programa, se puede utilizar de la siguiente manera:
```javascript
const numeros = require('./numeros');
```
Sin embargo, es importante destacar que este módulo no exporta ninguna función o variable, por lo que no se puede utilizar de manera directa en otro programa. Para utilizar este módulo, se debería modificar para exportar las funciones o variables necesarias.

Un ejemplo de uso del módulo "Numeros" sería:
```javascript
// Ejemplo de uso con JSON
const numeros = [];
for (let i = 0; i < 5; i++) {
  numeros.push(parseInt(prompt(`Ingrese un número: `)));
}
const vector = leerVector("Ejemplo");
console.log(vector);
```
Ten en cuenta que este ejemplo no es posible con el código actual, ya que el módulo "Numeros" no exporta la función `leerVector`. 

## 5. Dependencias
El módulo "Numeros" utiliza la siguiente dependencia:
- `prompt-sync`: biblioteca que permite obtener la entrada del usuario de manera síncrona.

La versión utilizada de `prompt-sync` es `4.2.0`, como se especifica en el archivo `package.json`.