# Predicción de Riesgo de Inundaciones - Ecuador (Grupo 2)
Este proyecto implementa modelos de Machine Learning para predecir la probabilidad de inundaciones en distintas zonas de Ecuador. La solución integra el análisis de datos meteorológicos y geográficos con una aplicación web interactiva desplegada en la nube.

Demo en vivo : https://proyecto-inundaciones-grupo-2.onrender.com/

# Objetivo del Proyecto
Clasificar si una zona geográfica específica presenta riesgo de inundación (1) o no (0), basándose en el impacto humano histórico y variables climáticas, para asistir en la toma de decisiones preventivas.

# Metodología y Datos
1. Fuentes de Datos
El dataset final se construyó integrando tres fuentes oficiales:

Histórico de Eventos (2010–2023): Base de eventos adversos (SNGRE) filtrada por CAUSA: Lluvias y EVENTO: Inundación. 
Clima: Dataset de precipitación subnacional (ecu-rainfall-subnat-full.csv).
Obetinido de : https://data.humdata.org/dataset/ecu-rainfall-subnational
Demografía: Listado de códigos postales y población por cantón,  (Datos obetenidos del Inec) 

# El modelo fue entrenado utilizando las siguientes variables predictoras clave seleccionadas en el notebook:
precipitacion_promedio_mm: Promedio histórico de lluvias por cantón.
Poblacion_Cantonal: Cantidad de habitantes (indicador de vulnerabilidad/exposición).
Coordenadas: (LATITUD, LONGITUD) utilizadas para la visualización geoespacial.

# Variable Objetivo (Target)
Se construyó una variable binaria riesgo_inundacion:
1 (Riesgo Alto): Si el evento histórico registró personas afectadas, damnificadas o fallecidas.
0 (Riesgo Bajo): Si no hubo impacto humano registrado.

# Modelos Evaluados
Se compararon varios algoritmos de clasificación usando GridSearchCV para optimización:
Random Forest Classifier (Modelo principal).
 Decision Tree Classifier.
 Logistic Regression.
 Voting Classifier (Ensamble).

# Stack Tecnológico
Lenguaje: Python 3.x
ML & Data: Pandas, NumPy, Scikit-learn (Entrenamiento y validación).
Backend: Flask (Servidor web).
Frontend & Mapas:
Leaflet.js: Librería de JavaScript para el renderizado del mapa interactivo (no se usó Folium, sino integración directa de JS en plantillas Jinja2).
HTML/CSS: Interfaz de usuario y plantillas.
Infraestructura: Render (Despliegue en la nube).
