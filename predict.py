import os
import joblib
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ruta_modelo = os.path.join(BASE_DIR, 'modelo_predictor.pkl')

artefactos = joblib.load(ruta_modelo)
modelo = artefactos['modelo']
scaler = artefactos['scaler']
media_provincia = artefactos['media_provincia']
media_marca = artefactos['media_marca']
media_carroceria = artefactos['media_carroceria']
columnas = artefactos['columnas']
media_global = artefactos['media_global']


def predecir_precio(km, anio, provincia, marca, carroceria):
    antiguedad = 2026 - anio

    provincia_enc = media_provincia.get(provincia, media_global)
    marca_enc = media_marca.get(marca, media_global)
    carroceria_enc = media_carroceria.get(carroceria, media_global)

    entrada = pd.DataFrame([{
        'km': km,
        'antiguedad': antiguedad,
        'provincia_enc': provincia_enc,
        'marca_enc': marca_enc,
        'carroceria_enc': carroceria_enc,
    }])[columnas]

    entrada_escalada = scaler.transform(entrada)
    return modelo.predict(entrada_escalada)[0]


def elegir_opcion(opciones, nombre):
    print(f"\nElegí {nombre}:")
    for i, opcion in enumerate(opciones, start=1):
        print(f"{i}. {opcion}")
    indice = int(input("Número: ")) - 1
    return opciones[indice]


if __name__ == "__main__":
    km = float(input("Kilometraje: "))
    anio = int(input("Año: "))

    provincias_disponibles = list(media_provincia.index)
    marcas_disponibles = list(media_marca.index)
    carrocerias_disponibles = list(media_carroceria.index)

    provincia = elegir_opcion(provincias_disponibles, "provincia")
    marca = elegir_opcion(marcas_disponibles, "marca")
    carroceria = elegir_opcion(carrocerias_disponibles, "carrocería")

    precio = predecir_precio(km, anio, provincia, marca, carroceria)
    print(f"\nPrecio estimado: USD {precio:,.2f}")
