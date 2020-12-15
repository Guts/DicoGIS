# DicoGIS: el diccionario de datos SIG

O como crearse su propio DRAE de la información geográfica en 5 minutos y 3 clicks.
Les presento un pequeño herramienta sin ninguna pretensión sino de ser bien práctico para manejar sus datos.

![DicoGIS - Animated demonstration](../static/img/DicoGIS_demo.gif "DicoGIS - Animated demonstration")

## Presentación

[DicoGIS](https://github.com/Guts/DicoGIS) es un pequeño utilitario que produce un diccionario de datos al formato Excel 2003 (.xls). Disponible en ejecutable Windows (.exe) sin instalación requerida y en script (consultar las dependencias), se puede usar directamente desde una USB.

![DicoGIS - Logo](../static/img/DicoGIS_logo.png "DicoGIS - Logo")

Es muy útil para precisos casos:

- se le entrega una base de datos, tipo archivos o tipo PostGIS, dentro de la cual le gustaría saber lo que hay adentro;
- en el marco de su trabajo, le gustaría ofrecer fácilmente una lista de los datos entregados a sus colegas/partenarios/clientes.

## Características técnicas

En teoría, los formatos compatibles son todos que cuenta [GDAL](https://gdal.org/drivers/raster/index.html) e [OGR](https://gdal.org/drivers/vector/index.html) pero por el momento, aquí los implementados son:

- vectores: shapefile, tables MapInfo, GeoJSON, GML, KML
- rasters: ECW, GeoTIFF, JPEG
- bases de datos archivos ("flat"): Esri File GDB
- CAO: DXF (+ lista de los DWG)
- Documentos cartográficos: Geospatial PDF

El script Python es compatible con los mayores sistemas operativos:

- Ubuntu 12/14.04
- Windows 7/8.1
- Mac OS X (gracias a [GIS Blog Fr](https://twitter.com/gisblogfr/status/515068147901407232))

DicoGIS existe en [3 idiomas (Français, Anglais et Espagnol)](https://github.com/Guts/DicoGIS/tree/master/dicogis/locale/) pero es muy fácil de personalizar o añadir una traducción.

¿Qué tal los performancias? Eso si depende de la computadora que lo ejecute. Pero, para tener una idea, en la mía DicoGIS demora mas o menos 20 segundos para:

- una cuarentena de vectores,
- una decena de rasters (representando 90 Mo al total),
- 7 FileGDB conteniendo unos 60 vectores,
- y unos archivos DXF.

## Como usarlo

1. Descargar la última versión:

    - sea del [ejecutable Windows](https://github.com/Guts/DicoGIS/releases),
    - sea del [código fuente](https://github.com/Guts/DicoGIS/archive/master.zip).

2. Descomprimir y iniciar DicoGIS.exe / el script DicoGIS.py

    ![DicoGIS - Launch](../static/img/00a_DicoGIS_Win32exe.PNG "DicoGIS - Launch")

3. Cambiar el idioma

    ![DicoGIS - Switch language](../static/img/99_DicoGIS_SwitchLanguage.gif "DicoGIS - Switch language")

4. Segûn el tipo de datos que quieres analizar:

    - Para datos organizados en archivos:

        1. Escoger la carpeta principal: la exploración empieza y la barra de progresión continua hasta el fin del listing;
        2. Elegir los formatos deseados;

        ![DicoGIS - Listing](../static/img/02_DicoGIS_Listing.gif "DicoGIS - Listing")

    - Para datos almacenados en una base de datos PostgreSQL/PostGIS, es lo mismo principio excepto que se debe entrar los parámetros de conexión:

        ![DicoGIS - Processing PostGIS](../static/img/06_DicoGIS_PostGIS.gif "DicoGIS - Processing PostGIS")

5. Iniciar y esperar hasta el fin del proceso: guardar el archivo Excel generado.

    ![DicoGIS - Processing files](../static/img/05_DicoGIS_Processing.gif "DicoGIS - Processing files")

6. Consultar el archivo y arreglar los estilos según sus preferencias.

## ¿que tipo de informaciones para que tipo de datos?

El archivo Excel (2003 = .xls) contiene metadatos organizados en pestañas según el tipo de datos. Hice una [matrix resumiendo las informaciones para cada formato](../misc/formats_matrix.md).
