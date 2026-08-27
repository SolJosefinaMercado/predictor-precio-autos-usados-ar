# 🚗 Predictor de Precios de Autos Usados (Argentina)

Modelo de regresión que estima el precio de un auto usado en el mercado argentino a partir de kilometraje, año, provincia, marca y tipo de carrocería. Incluye scraping propio de datos, un pipeline completo de limpieza y feature engineering, y una interfaz web hecha con Gradio para probar el modelo.

Proyecto de portfolio — Tecnicatura en IA y Ciencia de Datos (ISSD).

> 🔗 **Demo en vivo:** _(agregar link una vez desplegado en Render)_

<!-- Sugerencia: reemplazar esto por un screenshot o GIF corto de la app funcionando -->
<!-- ![demo](assets/demo.gif) -->

## Por qué este proyecto

El mercado de autos usados en Argentina tiene una particularidad que lo vuelve un problema interesante para ciencia de datos: los precios se cotizan en dólares (o se ajustan constantemente contra el dólar) mientras que gran parte de las publicaciones online los muestra en pesos, en un contexto de inflación y brecha cambiaria. Un modelo que no tenga esto en cuenta queda desactualizado en semanas. Este proyecto está pensado para sostener su validez en el tiempo, no solo para acertar en el momento en que se entrenó.

## Fuente de datos y scraping

Los datos se obtienen scrapeando [autocosmos.com.ar](https://www.autocosmos.com.ar/auto/usado) (`scraper.py`, con `requests` + `BeautifulSoup`).

La idea original era usar la API pública de MercadoLibre, pero tras un cambio de política en abril de 2025 empezó a devolver `403 Forbidden`. En vez de descartar el proyecto o buscar un dataset ya armado, se resolvió construyendo un scraper propio desde cero — la primera vez que encaré web scraping, aprendiendo en el camino cómo manejar headers/User-Agent, paginación y parsing de HTML, en vez de copiar una solución hecha.

El scraper recorre 100 páginas de resultados, extrae marca, modelo, año, km, precio, moneda, ciudad y provincia, y descarta duplicados y filas con nulos antes de guardar el CSV crudo.

## El problema de la dolarización

Como los precios vienen mezclados en ARS y USD, `conversor.py` dolariza todo el dataset consultando la cotización del dólar blue del día vía [DolarAPI](https://dolarapi.com/). El modelo se entrena y predice siempre en USD, que es una referencia mucho más estable que el peso argentino.

Esa misma decisión resuelve el problema de que la predicción "se venza": la app (`app.py`) vuelve a consultar la cotización del dólar blue **en el momento de la consulta**, no la que había cuando se entrenó el modelo, y recién ahí convierte el precio en USD a ARS para mostrarlo. El modelo no envejece con la inflación porque nunca opinó en pesos.

## Limpieza y análisis exploratorio (iterativo)

La limpieza no fue un paso único sino un proceso iterativo de varias pasadas sobre los datos, documentado en `notebooks/ETL_KNN.ipynb`:

- **Errores evidentes de carga**: años imposibles (2027), y valores de `km` que se repetían idénticos en decenas de filas de marcas y modelos distintos (100, 21, 300) — la firma típica de un placeholder o un valor de fallback mal capturado por el scraper en lugar del dato real.
- **Outliers de precio**: se detectaron con boxplots por año y se separaron en dos grupos — los que tenían una explicación real (autos de alta gama, ej. Audi Q8, Mercedes) y los que eran errores de carga (un Fiat Cronos publicado en 1.23M de dólares).
- **Casos límite verificados uno por uno**: vehículos anteriores a 1980, y registros con menos de 1000 km declarados. Para estos casos, en vez de aplicar una regla genérica, usé a Claude como apoyo para consultar la veracidad de combinaciones específicas de marca/modelo/año/km/precio contra lo que se sabe del mercado real (por ejemplo, si tiene sentido que un Ford T de 1929 con 1000 km listado sea un auto de colección y no un error de tipeo).
- **Autos de colección**: identificados a partir de un scatter de antigüedad vs. kilometraje (baja cantidad de km con muchos años), separados como categoría propia en vez de tratarlos como outliers a eliminar.
- **Análisis estadístico de la variable geográfica**: un ANOVA mostró diferencias significativas en el precio promedio entre provincias (F=3.91, p<0.001), pero el test de Tukey HSD reveló que esas diferencias se concentran en unos pocos pares de provincias, no de forma generalizada. Conclusión: la provincia probablemente actúa como variable *proxy* de la composición del mercado local (qué marcas/modelos circulan ahí) más que como una causa directa del precio — se mantuvo en el modelo sujeta a validación empírica por RMSE/MAE/R².

Dataset final después de la limpieza: **4.614 registros**, con precios entre USD 1.000 y USD 76.900.

## Feature engineering: por qué carrocería y no "marca cruda"

`marca` tiene 47 valores distintos y `modelo` tiene 421. Ninguno de los dos es directamente utilizable: `modelo` aporta demasiado ruido (la mayoría con muy pocos registros), y agrupar solo por `marca` hace que el modelo pierda la jerarquía de precio *dentro* de cada marca — un Toyota Corolla y un Toyota Hilux quedan indistinguibles si solo se mira la marca, cuando en la práctica son segmentos de precio completamente distintos.

La solución fue construir una variable de **carrocería** (Hatchback, Sedán, SUV, Pickup, Coupé, etc.): se extrajeron los 421 pares únicos de marca/modelo, y se categorizó cada uno por tipo de carrocería con apoyo de Claude para acelerar y verificar la clasificación de un catálogo tan grande, resultando en 12 categorías con volumen suficiente para que el modelo aprenda de cada una.

## Encoding de variables categóricas

En vez de one-hot encoding (que con 47 marcas y 12 carrocerías infla mucho la dimensionalidad y no aporta noción de similitud, algo importante justamente para un modelo basado en distancias como KNN), se usó **target encoding**: cada categoría de `marca`, `provincia` y `carroceria` se reemplaza por el precio promedio de esa categoría, calculado únicamente con el set de entrenamiento (para evitar data leakage hacia el set de test).

Esto convierte cada categoría en un número que representa su posición relativa de precio frente a las demás — por ejemplo, "SUV" queda representado por un valor más alto que "Hatchback" porque en promedio los SUV son más caros — lo cual es exactamente el tipo de información que un modelo de vecinos más cercanos puede aprovechar para medir distancia entre autos comparables.

## Por qué KNN y no un ensamble de árboles

Antes de asentarme en KNN evalué Random Forest y Gradient Boosting. La decisión de quedarme con **KNeighborsRegressor** no fue solo por métricas, sino por cómo se corresponde con el problema real: cuando alguien tasa un auto usado —un concesionario, un tasador, o el propio dueño mirando el mercado— en la práctica lo hace comparándolo con autos similares que ya se vendieron o están publicados, no aplicando una regla de árboles de decisión. KNN modela ese razonamiento de forma directa: predice el precio de un auto en función de sus vecinos más cercanos en ese espacio de características (km, antigüedad, y las medias de precio de marca/provincia/carrocería).

Las variables se escalan con `StandardScaler` antes de calcular distancias (sin esto, `km` con valores de cientos de miles dominaría por completo la distancia frente a las demás columnas). El valor de `k` se optimizó recorriendo `k` de 1 a 40 y evaluando RMSE en cada uno.

**Resultado final** (`k=13`, `weights="distance"`, sobre el set de test):

| Métrica | Valor |
|---|---|
| MAE | USD 3.248 |
| RMSE | USD 5.490 |
| R² | 0.629 |

Para dimensionar la mejora: un KNN base sin la variable de marca daba R² 0.395 (MAE 4.480); agregar `marca` encodeada lo llevó a R² 0.608 (MAE 3.370); y optimizar `k` y el esquema de pesos lo llevó al resultado final de R² 0.629 (MAE 3.248) — cada decisión de feature engineering, no solo el algoritmo, movió la aguja.

## Interfaz

La app (`app.py`) usa **Gradio** con un tema oscuro personalizado en vez de la interfaz por defecto, para que la demo se vea como un producto y no como un notebook. El usuario completa kilometraje, año, provincia, marca y carrocería, y recibe el precio estimado en USD y su equivalente en ARS al dólar blue del momento.

## Estructura del proyecto

```
├── app.py                  # Interfaz Gradio
├── predict.py               # Carga el modelo entrenado y expone predecir_precio()
├── scraper.py                # Scraping de autocosmos.com.ar
├── conversor.py              # Dolarización del dataset crudo vía DolarAPI
├── config.py                  # Rutas y constantes centralizadas
├── modelo_predictor.pkl        # Modelo KNN + scaler + tablas de encoding (serializado)
├── requirements.txt
├── data/
│   ├── raw/                    # Salida cruda del scraper
│   └── processed/               # Dataset dolarizado
└── notebooks/
    ├── ETL_KNN.ipynb             # Limpieza, EDA, encoding, entrenamiento y evaluación
    ├── modelos_para_categorizar.csv  # Pares marca/modelo únicos, sin categorizar
    └── modelos_categorizados.csv     # Mismos pares, con carrocería asignada
```

> **Nota:** este repo incluye la app de inferencia (`predict.py` + el modelo ya entrenado) y el notebook con todo el proceso de limpieza, EDA y entrenamiento. No incluye un script `training.py` separado — el entrenamiento se hizo y se versiona dentro de `notebooks/ETL_KNN.ipynb`.

## Cómo correrlo localmente

```bash
git clone <url-del-repo>
cd predictor-autos-usados
pip install -r requirements.txt
python app.py
```

Para reejecutar el scraping o el notebook hace falta además `beautifulsoup4`, `plotly`, `scipy` y `statsmodels` (incluidos en `requirements.txt`).

> Si vas a correr `notebooks/ETL_KNN.ipynb` de cero (kernel reiniciado): la celda de encoding referencia una variable `media_categoria` que en el notebook tal cual quedó guardado no está definida — el nombre correcto, coherente con el resto del pipeline y con el modelo ya serializado, es `media_carroceria`. Quedó así de una refactorización de nombres a mitad de proceso.

## Limitaciones conocidas

- La antigüedad se calcula contra un año de referencia fijo (2026) en `predict.py`; a partir de 2027 hay que actualizarlo o calcularlo dinámicamente con la fecha actual.
- Los datos vienen de una sola fuente (autocosmos.com.ar); precios de otras plataformas pueden tener otra distribución.
- El modelo no tiene información sobre el estado real del vehículo (choques, service al día, único dueño, etc.) más allá de km y año — dos autos "iguales" en esos campos pueden valer distinto en la vida real.
- R² de 0.63 significa que todavía queda variabilidad del precio sin explicar; hay margen para sumar features o probar otros esquemas de encoding.

## Stack

Python · pandas · scikit-learn · Gradio · BeautifulSoup · Plotly · SciPy/statsmodels (ANOVA) · DolarAPI

## Próximos pasos

- Despliegue en Render.
- Actualizar el cálculo de antigüedad para que no dependa de un año hardcodeado.
- Reentrenar periódicamente con datos más recientes.
