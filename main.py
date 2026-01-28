import feedparser
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
import json
import random
import time
import sys
import urllib.request
import requests 

print("🚀 INICIANDO RADAR (MODO FOTOS REALES - EXTRACCIÓN RSS)...")

# --- 1. CONFIGURACIÓN ---
# Fuentes que suelen incluir fotos en sus feeds
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
    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
    print("✅ Credenciales OK.")
except Exception as e:
    print(f"❌ Error Config: {e}")
    sys.exit(1)

# --- 2. FUNCIÓN PARA EXTRAER FOTO REAL ---
def extract_image_from_rss(entry):
    # Intento 1: Media Content (Estándar RSS)
    if 'media_content' in entry:
        try:
            return entry.media_content[0]['url']
        except: pass
    
    # Intento 2: Media Thumbnail
    if 'media_thumbnail' in entry:
        try:
            return entry.media_thumbnail[0]['url']
        except: pass
        
    # Intento 3: Links de imagen (Enclosures)
    if 'links' in entry:
        for link in entry.links:
            if 'image' in link.type:
                return link.href
                
    return None

# --- 3. SELECCIONAR NOTICIA + FOTO ---
def get_one_story():
    print("📡 Buscando noticia con foto real...")
    candidates = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for url in RSS_URLS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                feed = feedparser.parse(response.read())
            
            for entry in feed.entries[:6]:
                # Buscamos la foto real
                real_img = extract_image_from_rss(entry)
                summary = entry.summary if hasattr(entry, 'summary') else entry.title
                
                # Solo aceptamos la noticia si tiene texto suficiente
                if len(summary) > 20:
                    candidates.append({
                        "titulo": entry.title,
                        "resumen": summary,
                        "foto_real": real_img # Guardamos la URL de la foto original
                    })
        except:
            pass
            
    if not candidates:
        return None
    
    # Elegimos una al azar
    return random.choice(candidates)

# --- 4. REDACCIÓN ---
def write_full_article(story_data):
    print("🧠 IA: Redactando reportaje...")
    
    prompt = f"""
    Eres un Periodista Senior de 'Radar Internacional'.
    
    NOTICIA:
    Titular: {story_data['titulo']}
    Datos: {story_data['resumen']}

    TAREA:
    Escribe un ARTÍCULO DE FONDO (4 párrafos largos) en ESPAÑOL NEUTRO.
    Extiende la información explicando el contexto.
    
    FORMATO DE SALIDA (Usa el separador ||||):
    TITULO_PROFESIONAL||||CONTENIDO_HTML

    REGLAS HTML:
    - Primer párrafo: <b>CIUDAD (Radar) —</b> ...
    - Usa <p> para párrafos.
    - No uses Markdown.
    """
    
    payload = { "contents": [{ "parts": [{"text": prompt}] }] }
    
    try:
        response = requests.post(API_URL, json=payload)
        
        if response.status_code != 200:
            print(f"❌ Error Google: {response.text}")
            return None
            
        result = response.json()
        texto = result['candidates'][0]['content']['parts'][0]['text']
        
        texto = texto.replace("```html", "").replace("```", "").strip()
        parts = texto.split("||||")
        
        if len(parts) >= 2:
            return {
                "titulo": parts[0].strip(),
                "contenido": parts[1].strip(),
                "foto": story_data['foto_real'] # Usamos la foto real que extrajimos antes
            }
        else:
            return None 
    except Exception as e:
        print(f"⚠️ Error IA: {e}")
        return None

# --- 5. PUBLICAR ---
def publish(article):
    if not article:
        print("❌ No hay artículo.")
        sys.exit(1)

    print(f"🚀 Publicando: {article['titulo']}")
    
    try:
        # Usamos la foto real. Si no hay (es None), usamos un placeholder genérico.
        img_url = article['foto']
        if not img_url:
            # Respaldo solo si la noticia original no traía foto
            ts = int(time.time())
            img_url = f"https://loremflickr.com/800/500/news/all?lock={ts}"
        
        # A veces las fotos de RSS son pequeñas, intentamos trucos para agrandarlas
        img_url = img_url.replace("144x144", "1024x576").replace("width=144", "width=800")

        html = f"""
        <div style="font-family: 'Georgia', serif; font-size: 19px; line-height: 1.8; color:#222;">
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 25px;">
                <img border="0" src="{img_url}" style="width:100%; max-width:800px; border-radius:5px;" alt="Imagen de la noticia"/>
                <br/><small style="font-family:Arial; font-size:10px; color:#666;">FOTO: AGENCIA / PRENSA</small>
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
        print("✅ ¡EXITO TOTAL! Noticia con foto real publicada.")
        
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
