# Jetson Nano Image to Text Server
Aplicación en Python para Jetson Nano que recive imagenes, hace inferencia sobre ellas y retorna al cliente una oración enumaerando las objetos detectados y la imagen con bounding boxes de los objetos detectados.
Retorna mensajes informativos en la consola sobre las conexiones activas y las operaciones que esta realizando:
![]{./start_up.png}{App start up and loading of model}
![]{./new_conn.png}{Init server and manage new connection}
## Requisitos 
Se debe tener instalado los siguientes elementos en el jetson nano
* Jetson Inference
* Jetson Utils
* Las siguientes librerías de Python:
    * uuid
    * shutil
    * inflect
    * socket

## Como funciona

Cuando se ejecuta el programa de servidor se carga el modelo de inferencia
deseado (SSD-Mobilenet-V2) y se mantiene en memoria a la espera de operaciones. Para la creación del servicio web, por medio de la librería "socket"de
Python, se crea un servidor que está esperando a nuevas conexiones TCP al
puerto previamente determinado. Cuando se registra una nueva conexión se
crea un hilo en donde se llevara a cabo el procesamiento y permite atender
otras conexiones al mismo tiempo. El proceso para atender una conexión
se detallara a continuación, se recibe un mensaje inicial que debe tener los
siguientes elementos:
* Extensión de la imagen: ".jpg"
* Separador: <SEP>
* Tamaño en bytes del archivo: "10000"
Una vez obtenidos estos datos se genera una cadena de caracteres aleatorios
con los que se crea una carpeta donde se almacenaran los archivos temporales. Se recibe la imagen en chunks de 4096 bytes y se guarda en un archivo
temporal. Por medio de la librería "jetson.utils"se carga el archivo temporal
con la imagen y con la librería "jetson.inference"se ejecuta la inferencia con
el modelo especificado y la imagen cargada. Una vez realizada la inferencia
se obtiene la imagen modificada que es guardada de manera temporal y una
lista con los objetos detectados en la imagen, se agrupan y contabilizan las incidencias de cada clase y se forma la oración por medio de la librería ïnflect".
Si no ocurrieron errores, se envía un mensaje al cliente con los siguientes
campos:
* Éxito en la operación: "True"
* Separador: <SEP>
* Tamaño en bytes del archivo: "10000"
* Separador: <SEP>
* Oración generada: "Se detectaron los siguientes objetos: ..."
Luego de enviar este mensaje se envía la imagen procesada al cliente en
chunks de 4096 bytes. En caso de error se envía un mensaje con los siguientes
campos:
* éxito en la operación: "False"
* Separador: <SEP>
* Tamaño en bytes del archivo: "0"
* Separador: <SEP>
* Oración generada: .Ocurrió el siguiente error: ..."
Para finalizar, se cierra la conexión TCP del socket con el cliente y se elimina la carpeta con los archivos temporales.