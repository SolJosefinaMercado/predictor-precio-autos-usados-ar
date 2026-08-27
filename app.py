import os
import gradio as gr
import requests
from predict import predecir_precio, media_provincia, media_marca, media_carroceria

# las opciones de los dropdowns salen directo de las tablas de encoding,
# así siempre coinciden con lo que el modelo realmente conoce
provincias_disponibles = sorted(media_provincia.index)
marcas_disponibles = sorted(media_marca.index)
carrocerias_disponibles = sorted(media_carroceria.index)

# --- Tema oscuro custom, basado en el tema Base de Gradio ---
tema_oscuro = gr.themes.Base(
    primary_hue="cyan",
    secondary_hue="slate",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui"],
).set(
    body_background_fill="#0f172a",
    body_background_fill_dark="#0f172a",
    block_background_fill="#1e293b",
    block_background_fill_dark="#1e293b",
    block_border_width="1px",
    block_border_color="#334155",
    block_label_text_color="#94a3b8",
    body_text_color="#e2e8f0",
    body_text_color_dark="#e2e8f0",
    input_background_fill="#0f172a",
    button_primary_background_fill="#06b6d4",
    button_primary_background_fill_hover="#0891b2",
    button_primary_text_color="#0f172a",
    block_radius="16px",
    input_radius="10px",
    button_large_radius="10px",
)

css_extra = """
#titulo { text-align: center; margin-bottom: 0px; }
#titulo h1 { font-size: 2.4rem; margin-bottom: 0.2rem; }
#subtitulo { text-align: center; color: #94a3b8 !important; margin-bottom: 1.5rem; }
.gradio-container { max-width: 820px !important; margin: auto; }
footer { visibility: hidden; }

/* tarjeta de inputs con sombra sutil */
#panel-inputs, #panel-resultado {
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    border-radius: 16px !important;
}

/* tarjeta de resultado */
#tarjeta-resultado {
    background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
    border-radius: 16px;
    padding: 28px 20px;
    text-align: center;
    color: #0f172a;
    animation: fadeIn 0.4s ease-in-out;
}
#tarjeta-resultado .precio-usd {
    font-size: 2.1rem;
    font-weight: 700;
    margin: 0;
}
#tarjeta-resultado .precio-ars {
    font-size: 1.1rem;
    font-weight: 500;
    margin-top: 6px;
    opacity: 0.85;
}
#tarjeta-resultado .cotizacion {
    font-size: 0.8rem;
    margin-top: 10px;
    opacity: 0.7;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
}
"""

TARJETA_INICIAL = """
<div id="tarjeta-resultado" style="opacity:0.6;">
    <p class="precio-usd">💰 —</p>
    <p class="precio-ars">Completá los datos y presioná "Estimar precio"</p>
</div>
"""


def obtener_cotizacion_blue():
    # misma fuente (DolarAPI) y misma cotización (blue, venta) que se usó
    # para dolarizar el dataset original — así la conversión es consistente
    try:
        respuesta = requests.get("https://dolarapi.com/v1/dolares/blue", timeout=5)
        respuesta.raise_for_status()
        return respuesta.json()["venta"]
    except Exception:
        return None


def predecir(km, anio, provincia, marca, carroceria):
    precio_usd = predecir_precio(km, anio, provincia, marca, carroceria)
    cotizacion = obtener_cotizacion_blue()

    if cotizacion is not None:
        precio_ars = precio_usd * cotizacion
        linea_ars = f'<p class="precio-ars">🇦🇷 ARS {precio_ars:,.2f}</p>'
        linea_cotizacion = f'<p class="cotizacion">Dólar blue (venta): ${cotizacion:,.2f}</p>'
    else:
        linea_ars = '<p class="precio-ars">No se pudo obtener la cotización del dólar.</p>'
        linea_cotizacion = ""

    return f"""
    <div id="tarjeta-resultado">
        <p class="precio-usd">💰 USD {precio_usd:,.2f}</p>
        {linea_ars}
        {linea_cotizacion}
    </div>
    """


with gr.Blocks(title="Predictor de Precio de Autos") as demo:
    gr.Markdown("# 🚗 Predictor de Precio de Autos Usados", elem_id="titulo")
    gr.Markdown(
        "Modelo KNN entrenado sobre autos usados de Argentina, scrapeados y dolarizados. "
        "Proyecto de portfolio — Tecnicatura en IA y Ciencia de Datos (ISSD).",
        elem_id="subtitulo",
    )

    with gr.Row():
        with gr.Column(elem_id="panel-inputs"):
            with gr.Group():
                km = gr.Number(label="Kilometraje", minimum=0, value=80000)
                anio = gr.Number(label="Año", minimum=1990, maximum=2026, value=2018, precision=0)
                provincia = gr.Dropdown(choices=provincias_disponibles, label="Provincia")
                marca = gr.Dropdown(choices=marcas_disponibles, label="Marca")
                carroceria = gr.Dropdown(choices=carrocerias_disponibles, label="Carrocería")
            boton = gr.Button("Estimar precio 🔍", variant="primary", size="lg")

        with gr.Column(elem_id="panel-resultado"):
            resultado = gr.HTML(value=TARJETA_INICIAL)
            gr.Examples(
                examples=[
                    [110000, 2014, "Buenos Aires (A.M.B.A.)", "Peugeot", "Hatchback"],
                    [43000, 2020, "Buenos Aires (A.M.B.A.)", "Chevrolet", "SUV"],
                    [149000, 2014, "Buenos Aires (A.M.B.A.)", "BMW", "Sedán"],
                ],
                inputs=[km, anio, provincia, marca, carroceria],
                label="Ejemplos rápidos",
            )

    boton.click(fn=predecir, inputs=[km, anio, provincia, marca, carroceria], outputs=resultado)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.launch(theme=tema_oscuro, css=css_extra, server_name="0.0.0.0", server_port=port)
