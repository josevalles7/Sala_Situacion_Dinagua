El modelo en python está dividido en "one_steap" que contiene los cálculos del modelo y el script principal que se llama "sacramento_(tipo de calibración)" que importa funciones de "one_steap". En el caso de la calibración con SCE-UA el algoritmo está en un script a parte llamado "SCE-UA" y el script "sacrameno_SCE-UA" importa sus funciones. 
En las carpetas Sacramento_sceua y Sacramento_PSO se puede correr el script sacramento para calibrar el modelo.
El hidrograma unitario y los datos observados estan en el archivo parametros_cuenca y datos_procesados en la carpeta Caracteristicas_cuenca_y_datos.
Para graficar los resultados de un set específico de parámetros se puede utilizar el script que está en la carpeta Sacramento_manual.
