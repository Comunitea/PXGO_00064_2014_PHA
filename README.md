Exiten dos configuraciones para el buildout buildoutPHA_NOPG.cfg no instala postgres dentro del entorno virtual y no lo gestiona bajo supervisor. En este caso es necsario entrar modificar el script par aadecuarlo al postgres al que se debe conectar. ATENCIÓN: Las modificaciones en este sript no deben subirse posteriormente a este repositorio
El otro archivo buildoutPHA.cfg sí instala postgres y no es necesario (ni se debe) modificar nada sobre él, salvo que sea alguna propuesta de mejora de la configuración o gestión

# Buildout base para proyectos con OpenERP y PostgreSQL
OpenERP master en el base, PostgreSQL 9.3.4 y Supervisord 3.0
- Buildout crea cron para iniciar Supervisord después de reiniciar (esto no lo he probado)
- Supervisor ejecuta PostgreSQL, más info http://supervisord.org/
- También ejecuta la instancia de PostgreSQL
- Si existe un archivo dump.sql, el sistema generará la base de datos con ese dump
- Si existe  un archivo frozen.cfg es el que se debeía usar ya que contiene las revisiones aprobadas
- PostgreSQL se compila y corre bajo el usuario user (no es necesario loguearse como root), se habilita al autentificación "trust" para conexiones locales. Más info en more http://www.postgresql.org/docs/9.3/static/auth-methods.html
- Existen plantillas para los archivo de configuración de Postgres que se pueden modificar para cada proyecto.


# Uso (adaptado)
En caso de no haberse hecho antes en la máquina en la que se vaya a realizar, instalar las dependencias que mar Anybox
- Añadir el repo a /etc/apt/sources.list:
```
$ deb http://apt.anybox.fr/openerp common main
```
- Si se quiere añadir la firma. Esta a veces tarda mucho tiempo o incluso da time out. Es opcional meterlo
```
$ sudo apt-key adv --keyserver hkp://subkeys.pgp.net --recv-keys 0xE38CEB07
```
- Actualizar e instalar
```
$ sudo apt-get update
$ sudo apt-get install openerp-server-system-build-deps
```
- Para poder compilar e instalar postgres (debemos valorar si queremos hacerlo siempre), es necesario instalar el siguiente paquete (no e sla solución ideal, debería poder hacerlo el propio buildout, pero de momento queda así)
```
$ sudo apt-get install libreadline-dev
```
- Descargar el  repositorio de buildouts :
```
$ git clone https://github.com/Pexego/PXGO_00064_2014_PHA.git <ubicacion_local_repo>
```
- [EN REVISIÓN] Hacer checkout de la rama deseada según proyecto
```
$ git checkout master
```
- Crear un virtualenv dentro de la carpeta del respositorio. Esto podría ser opcional, obligatorio para desarrollo o servidor de pruebas, tal vez podríamos no hacerlo para un despliegue en producción. Si no está instalado, instalar el paquete de virtualenv
```
$ sudo apt-get install python-virtualenv
$ cd <ubicacion_local_repo>
$ virtualenv sandbox --no-setuptools
```
- Crear la carpeta eggs (no se crea al vuelo, ¿debería?
```
$ mkdir eggs
```
- Ahora procedemos a ehecutar el buildout en nuestro entorno virtual
```
$ sandbox/bin/python bootstrap.py -c <configuracion_elegida> --setuptools-version=40.8.0
```
- Ejecutar Supervisor, encargado de lanzar los servicios postgresql y odoo
```
$ bin/supervisord
```
- No crea carpeta project-addons, crearla a mano
```
$ mkdir project-addons
```
- Y por último
```
$ bin/buildout -c <configuracion_elegida>
```
- Urls
- Supervisor : http://localhost:9003
- Odoo: http://localhost:9169
      admin//admin

## Configurar OpenERP
Archivo de configuración: etc/openerp.cfg, si sequieren cambiar opciones en  openerp.cfg, no se debe editar el fichero,
si no añadirlas a la sección [openerp] deñ buildout.cfg
y establecer esas opciones .'add_option' = value, donde 'add_option'  y ejecutar buildout otra vez.

Por ejmplo: cambiar el nivel de logging de OpenERP
```
'buildout.cfg'
...
[openerp]
options.log_handler = [':ERROR']
...
```

Si se quiere jeecutar más de una instancia de OpenERP, se deben cambiar los puertos,
please change ports:
```
openerp_xmlrpc_port = 9169  (8069 default openerp)
openerp_xmlrpcs_port = 8071 (8071 default openerp)
supervisor_port = 9003      (9001 default supervisord)
postgres_port = 5434        (5432 default postgres)
```

# TODO
- Generar Apache and Nginx config for virualhost with Buildout

# Análisis estático de código con Sonarqube

Podemos efectuar un análisis con Sonarqube usando Docker sin necesidad de disponer de un servicio alojado siguiendo las indicaciones de este proyecto

https://github.com/newtmitch/docker-sonar-scanner

1. Levantamos servicio de Sonar dockerizado

```console
$ docker run -d --name sonarqube -p 9000:9000 -p 9092:9092 sonarqube
```

2. Esperamos que el servicio de sonar esté disponible en esta url http://localhost:9000

3. Ejecutamos el análisis

```console
$ docker run -ti -v $(pwd):/usr/src --link sonarqube newtmitch/sonar-scanner
```

Una vez finalizado el proceso análisis, tendremos disponible el proyecto y sus métricas en http://localhost:9000/dashboard?id=MyProjectKey . También se creará el directorio `.scannerwork` en el raíz de nuestro repositorio. Se puede (y se debe) borrar este directorio tras el análisis.

Si disponemos de un sistema OS/X o Windos el análisis puede tardar demasiado. Podemos acelerar el proceso ejecutando el análisis de esta forma:

```console
$ docker run --rm -ti -v $(pwd):/tmp/src:cached --link sonarqube newtmitch/sonar-scanner bash -c "cp -rp /tmp/src/ /usr/src; sonar-scanner -Dsonar.projectBaseDir=/usr/src"
```

# Contributors

IT (PH)

## Creators

Rastislav Kober, http://www.kybi.sk

