# SCRAPER DE AUTOS USADOS DE AUTOCOSMOS.COM.AR

from config import URL_BASE, HEADERS, RAW_DATA_PATH
import requests                     # libreria para hacer requests HTTP
from bs4 import BeautifulSoup       # libreria para interpretar HTML
import time                         # libreria para hacer pausas entre requests
import pandas as pd                 # libreria para trabajar con dataframes


headers = HEADERS
url_base = URL_BASE
autos = []                          # aca se alojará el listado de autos que se van a scrapear

for pagina in range(1, 101):
    params = {"pidx": pagina}
    response = requests.get(url_base, params=params, headers=headers)
                                    # get hace la peticion HTTP, python → autocosmos HTML → python
                                    # resultado alojado en response, que es un objeto de la libreria requests
    print(f'🤖⚙️ Scrapeando página {pagina} de 100...')
    print(response.status_code, len(response.text))     
                                    # 200 (codigo http), 245935 (n_caracteres del HTML)
    
    soup = BeautifulSoup(response.text, "html.parser")
                                    # interpreta el HTML y lo convierte en un objeto de la libreria BeautifulSoup
    avisos = soup.find_all("div", class_="listing-card__content")
                                    # busca todos los divs que tengan la clase listing-card__content, que es donde se encuentra la info de cada auto
                                    # find_all devuelve una lista de objetos BeautifulSoup, cada uno representando un aviso de auto
                                    # esa lista la recorremos con un for para extraer la info de cada aviso y guardarla en un diccionario, que luego agregamos a la lista autos
    
    for aviso in avisos:            # procesa un aviso de auto a la vez

        marca_tag = aviso.find("span", class_="listing-card__brand")
        modelo_tag = aviso.find("span", class_="listing-card__model")
        anio_tag = aviso.find("span", class_="listing-card__year")
        km_tag = aviso.find("span", class_="listing-card__km")
        ciudad_tag = aviso.find("span", class_="listing-card__city")
        provincia_tag = aviso.find("span", class_="listing-card__province")
        precio_tag = aviso.find("span", class_="listing-card__price-value")
        moneda_tag = aviso.find("meta", itemprop="priceCurrency")
        
        autos.append({              # limpia los strings y covierte cada tag 
            "marca": marca_tag.text.strip() if marca_tag else None,
            "modelo": modelo_tag.text.strip() if modelo_tag else None,
            "anio": int(anio_tag.text.strip()) if anio_tag else None,
            "km": int(km_tag["content"].replace("KMT ", "")) if km_tag and km_tag.has_attr("content") else None,
            "precio": float(precio_tag["content"]) if precio_tag and precio_tag.has_attr("content") else None,
            "moneda": moneda_tag["content"] if moneda_tag else None,
            "ciudad": ciudad_tag.text.split("|")[0].strip() if ciudad_tag else None,
            "provincia": provincia_tag.text.strip() if provincia_tag else None,
            })
    
    time.sleep(2)  


df = pd.DataFrame(autos)

# chequeo de nulos 
print(f'✅ Shape inicial: {df.shape[0]}')
print()
print(f'✅ Chequeo de nulos:\n{df.isnull().sum()}')
print()
print(f'✅ Chequeo de duplicados:\n Existen {df.duplicated().sum()} filas duplicadas en el DataFrame.')
print()
print(f'⏳🧹Limpieza de duplicados y nulos⏳🧹')
df.drop_duplicates(inplace=True)
df.dropna(inplace=True)
print()
print(f'✅ Shape posterior drop_duplicates y dropna: {df.shape[0]}')

df.to_csv(RAW_DATA_PATH, index=False)

print(f'✅ ARCHIVO CSV LISTO EN: {RAW_DATA_PATH}')
print()


