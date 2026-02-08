import feedparser
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
import json
import random
import time
import sys
import urllib.parse
import requests 
import urllib.parse

print("🚀 INICIANDO RADAR (GEMINI DIRECTO + FOTO IA)...")

# --- 1. CONFIGURACIÓN ---
RSS_URLS = [
    "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada",
    "https://www.bbc.com/mundo/temas/internacional/index.xml"
]

try:
    token_info = json.loads(os.environ["GOOGLE_TOKEN"])
    creds = Credentials.from_authorized_user_info(token_info)
    service = build('blogger', 'v3', credentials=creds)
    BLOG_ID = os.environ["BLOG_ID"]
    API_KEY = os.environ["GEMINI_API_KEY"]
    # URL directa a Gemini 1.5 Flash
    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={API_KEY}"
    print("✅ Credenciales OK.")
except Exception as e:
    print(f"❌ Error Config: {e}")
    sys.exit(1)

# --- 2. SELECCIONAR NOTICIA ---
def get_one_story():
    print("📡 Buscando noticia...")
    candidates = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for url in RSS_URLS:
        try:
            # Usamos requests en lugar de urllib para ser más modernos
            resp = requests.get(url, headers=headers, timeout=10)
            feed = feedparser.parse(resp.content)
            
            for entry in feed.entries[:5]:
                summary = entry.summary if hasattr(entry, 'summary') else entry.title
                if len(summary) > 20:
                    candidates.append(f"TITULAR: {entry.title}\nDATOS: {summary}")
        except:
            pass
            
    if not candidates:
        return None
    return random.choice(candidates)

# --- 3. REDACCIÓN (AQUÍ ES DONDE TÚ MANDAS) ---
def write_full_article(story_data):
    print("🧠 IA: Redactando reportaje...")
    
    prompt = f"""
    Eres Periodista de 'Radar Internacional'.
    NOTICIA: {story_data}

   TU MISIÓN:
    Escribe un ARTÍCULO DE FONDO (Mínimo 4 párrafos largos) en ESPAÑOL NEUTRO.
    No hagas un resumen simple. Agrega contexto, antecedentes y análisis.

    REGLAS DE FORMATO:
    1. **Título:** Periodístico y serio.
    2. **Imagen:** Crea un PROMPT VISUAL en INGLÉS para generar una foto realista.
    
    REGLAS PARA EL PROMPT DE LA FOTO:
    - Debe ser en INGLÉS.
    - Describe la ESCENA, no el concepto. (Mal: "Economy". Bien: "A busy stock market graph on a monitor, blurred office background").
    - NO uses nombres de personas famosas (la IA las deforma). Usa descripciones (ej: "A senior politician in a suit giving a speech").
    - Añade al final: ", photorealistic, 8k, news photography style".

    3. **Texto:** Usa negritas (<b>) para resaltar lo importante.
   
    FORMATO DE SALIDA (Usa separador ||||):
    TITULO||||PROMPT_VISUAL_INGLES||||CONTENIDO_HTML

    REGLAS HTML:
    - Primer párrafo: <b>CIUDAD (Radar) —</b> ...
    - Usa <p> y <b>. No Markdown.
    """
    
    payload = { "contents": [{ "parts": [{"text": prompt}] }] }
    
    try:
        response = requests.post(API_URL, json=payload)
        result = response.json()
        texto = result['candidates'][0]['content']['parts'][0]['text']
        
        texto = texto.replace("```html", "").replace("```", "").strip()
        parts = texto.split("||||")
        
        if len(parts) >= 3:
            return {
                "titulo": parts[0].strip(),
                "foto_prompt": parts[1].strip(),
                "contenido": parts[2].strip()
            }
        else:
            return None 
    except Exception as e:
        print(f"⚠️ Error IA: {e}")
        return None
        
# --- 4. PUBLICAR CON FOTO IA GENERADA ---
def publish(article):
    if not article:
        print("❌ No hay artículo.")
        sys.exit(1)

    print(f"🚀 Generando Imagen y Publicando: {article['titulo']}")
    
    try:
        # GENERACIÓN DE IMAGEN CON POLLINATIONS (MODELO FLUX)
        # Codificamos el prompt que nos dio Gemini para que sea una URL válida
        prompt_imagen = urllib.parse.quote(article['foto_prompt'])
        
        # Añadimos una semilla aleatoria para que la foto siempre sea distinta
        seed = random.randint(1, 99999)
        
        # URL Mágica: Usa el modelo 'flux' que es ultra realista
        img_url = f"https://image.pollinations.ai/prompt/{prompt_imagen}?width=1280&height=720&model=flux&nologo=true&seed={seed}"
        
        html = f"""
        <div style="font-family: 'Georgia', serif; font-size: 19px; line-height: 1.8; color:#111;">
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 25px;">
                <img border="0" src="{img_url}" style="width:100%; max-width:800px; border-radius:5px;" alt="Imagen generada por IA"/>
                <br/><small style="font-family:Arial; font-size:10px; color:#666;">IMAGEN GENERADA POR IA (FLUX)</small>
            </div>
            {article['contenido']}
            <br><hr>
            <p style="font-size:12px; color:#666; text-align:center;">Radar Internacional © 2026</p>
        </div>
        """
        
        body = {
            "kind": "blogger#post",
            "title": article["titulo"],
            "content": html,
            "labels": ["Internacional", "Noticias"]
        }
        
        service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print("✅ ¡EXITO TOTAL!")
        
    except Exception as e:
        print(f"❌ Error publicando: {e}")
        sys.exit(1)


if __name__ == "__main__":
    story = get_one_story()
    if story:
        art = write_full_article(story)
        publish(art)
    else:
        print("❌ Error RSS")
        sys.exit(1)
