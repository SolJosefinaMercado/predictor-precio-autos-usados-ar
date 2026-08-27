import requests
import pandas as pd
from config import RAW_DATA_PATH , PROCESSED_DATA_PATH

#---------------------------------------------------------------
# llamo la api para obtener la cotización del dólar blue al dia
#---------------------------------------------------------------
def obtener_cotizacion_dolar():
    response = requests.get("https://dolarapi.com/v1/dolares/blue")
    cotizacion = response.json()
    return cotizacion["venta"]  
#---------------------------------------------------------------
# proceso de dolarización de los precios
#---------------------------------------------------------------
def dolarizar_precio(row, valor_dolar):
    if row["moneda"] == "ARS":
        return row["precio"] / valor_dolar
    else:
        return row["precio"]
#---------------------------------------------------------------
# procesamiento del dataset: obtengo cotización del dólar y aplico la función de conversión
#---------------------------------------------------------------
def procesar_dataset():
    valor_dolar = obtener_cotizacion_dolar()
    print(f"Dólar blue a la fecha: {valor_dolar}")
    df = pd.read_csv(RAW_DATA_PATH)
    df["precio_usd"] = df.apply(lambda row: dolarizar_precio(row, valor_dolar), axis=1)
    df = df.drop(columns=["precio",'moneda'])
    df_dolarizado = df.copy()
    df_dolarizado.to_csv(PROCESSED_DATA_PATH, index=False)
    print(f'✅ Archivo CSV dolarizado guardado en {PROCESSED_DATA_PATH}')

    return df_dolarizado

if __name__ == "__main__":
    procesar_dataset()
    