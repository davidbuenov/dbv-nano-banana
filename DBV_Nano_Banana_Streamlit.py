# para ejecutarlo localmente:
# pip install -r requirements.txt
# streamlit run DBV_NanoBanana_Streamlit.py
import os
import io
import mimetypes
from datetime import datetime

import streamlit as st
from PIL import Image

from google import genai
from google.genai import types

st.markdown("""
<style>
.stAppDeployButton { display: none !important; }
[data-testid="stMainMenu"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="DBV Nano Banana UI", page_icon="🍌", layout="centered")
st.title("🍌 DBV Nano Banana (Gemini 2.5 Flash Image)")

with st.sidebar:
    st.header("Configuración")
    api_key_input = st.text_input("GEMINI_API_KEY", type="password", help="Tu clave de Google AI (no se guarda).")
    set_env = st.checkbox("Guardar en variable de entorno (sesión actual)", value=True)
    output_dir = st.text_input("Carpeta de salida", value="outputs")
    os.makedirs(output_dir, exist_ok=True)

st.markdown("Ingresa un prompt, añade imágenes de referencia opcionales y genera.")

prompt = st.text_area(
    "Prompt",
    value="Photorealistic close-up shot of a fluffy shih tzu playing with a small red rubber ball on a sandy beach at golden hour; the dog is mid-motion with sand particles flying, wet nose, detailed fur texture with slight saltwater dampness, joyful expression, ears flapping; warm sunset light casting soft long shadows, gentle ocean waves and subtle footprints in the background, shallow depth of field with creamy bokeh; captured with a professional full-frame camera, 50mm prime lens at f/1.8, ISO 100, natural white balance, high dynamic range, ultra-detailed, high-resolution.",
    height=120,
)

ref_images = st.file_uploader(
    "Imágenes de referencia (opcional, hasta 3)",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True,
)
if ref_images and len(ref_images) > 3:
    st.warning("Solo se usarán las 3 primeras imágenes.")
    ref_images = ref_images[:3]

col1, col2 = st.columns(2)
with col1:
    gen_button = st.button("Generar imagen", type="primary")
with col2:
    show_cost_info = st.checkbox("Mostrar info de costos", value=True)

def estimate_cost(num_images, cost_per_image=0.039):
    return num_images * cost_per_image

def pil_to_bytes(img: Image.Image, fmt="PNG"):
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()

def build_flat_payload(prompt_text, image_files):
    """
    Devuelve una lista 'plana' apta para contents:
    [Part.from_bytes(...), Part.from_bytes(...), ..., prompt_text]
    Sin Content(parts=[...]) y sin Part.from_text.
    """
    parts_or_strings = []
    for uploaded in image_files or []:
        img = Image.open(uploaded).convert("RGB")
        img_bytes = pil_to_bytes(img, fmt="PNG")
        parts_or_strings.append(
            types.Part.from_bytes(
                data=img_bytes,
                mime_type="image/png",
            )
        )
    parts_or_strings.append(prompt_text)
    return parts_or_strings

if gen_button:
    api_key = api_key_input.strip()
    if not api_key:
        st.error("Configura GEMINI_API_KEY en la barra lateral.")
        st.stop()

    if set_env:
        os.environ["GEMINI_API_KEY"] = api_key

    if not prompt.strip():
        st.error("Ingresa un prompt.")
        st.stop()

    client = genai.Client(api_key=api_key)

    # Opción A: payload “plano” cuando hay imágenes; string cuando no
    if ref_images:
        try:
            payload = build_flat_payload(prompt, ref_images)
        except Exception as e:
            st.error(f"Error procesando imágenes de referencia: {e}")
            st.stop()
    else:
        payload = prompt  # string simple

    config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"]
    )

    with st.spinner("Generando..."):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-image-preview",
                contents=payload,
                config=config,
            )
        except Exception as e:
            st.error(f"Error de la API: {e}")
            st.stop()

    images_saved = []
    texts = []
    if hasattr(response, "candidates") and response.candidates:
        for i, cand in enumerate(response.candidates):
            cont = getattr(cand, "content", None)
            if not cont or not getattr(cont, "parts", None):
                continue
            for j, part in enumerate(cont.parts):
                inline_data = getattr(part, "inline_data", None)
                if inline_data and getattr(inline_data, "data", None):
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    ext = mimetypes.guess_extension(getattr(inline_data, "mime_type", "image/png")) or ".png"
                    fname = os.path.join(output_dir, f"nanobanana_{ts}_{i}_{j}{ext}")
                    with open(fname, "wb") as f:
                        f.write(inline_data.data)
                    images_saved.append(fname)
                text = getattr(part, "text", None)
                if text:
                    texts.append(text)

    if images_saved:
        st.success(f"Éxito: {len(images_saved)} imagen(es) generada(s).")
        if show_cost_info:
            st.info(f"Costo estimado: ${estimate_cost(len(images_saved)):.4f} USD")
        for path in images_saved:
            st.image(path, caption=path, use_container_width=True)
    else:
        st.warning("No se generaron imágenes. Prueba con un prompt más concreto o revisa la API key y cuotas.")
        if show_cost_info:
            st.info("Costo estimado: $0.0000 USD")

    if texts:
        st.subheader("Texto devuelto")
        for t in texts:
            st.write(t)
