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
import urllib.parse

print("🚀 INICIANDO RADAR (MODELO FLASH 1.5 FORZADO)...")

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
    
    # URL FIJA AL MODELO GRATUITO (Nunca falla)
    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
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
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                feed = feedparser.parse(response.read())
            
            for entry in feed.entries[:6]:
                # Buscamos noticias con algo de texto
                summary = entry.summary if hasattr(entry, 'summary') else entry.title
                if len(summary) > 25:
                    candidates.append(f"TITULAR: {entry.title}\nRESUMEN: {summary}")
        except:
            pass
            
    if not candidates:
        return None
    # Elegimos una al azar para variar
    return random.choice(candidates)

# --- 3. REDACCIÓN (VIA HTTP DIRECTA) ---
def write_full_article(story_data):
    print("🧠 IA: Redactando reportaje...")
    
    prompt = f"""
    Eres el Editor Jefe de 'Radar Internacional'.
    
    NOTICIA A CUBRIR:
    {story_data}

    INSTRUCCIONES DE REDACCIÓN:
    1. Escribe un ARTÍCULO LARGO (Mínimo 4 párrafos bien desarrollados).
    2. Idioma: ESPAÑOL NEUTRO.
    3. Estilo: Serio, periodístico, informativo.
    4. FOTO: Describe la imagen perfecta para esta noticia en INGLÉS (ej: "Donald Trump speaking at podium, photorealistic").

    ESTRUCTURA DE RESPUESTA (Usa el separador ||||):
    TITULO_PROFESIONAL||||DESCRIPCION_FOTO_INGLES||||CONTENIDO_HTML

    REGLAS HTML:
    - Párrafo 1: <b>CIUDAD (Radar) —</b> ...
    - Usa <p> para párrafos.
    - Usa negritas <b> para resaltar datos clave.
    - NO uses Markdown.
    """
    
    payload = { "contents": [{ "parts": [{"text": prompt}] }] }
    
    try:
        response = requests.post(API_URL, json=payload)
        
        if response.status_code != 200:
            print(f"❌ Error Google ({response.status_code}): {response.text}")
            return None
            
        result = response.json()
        texto = result['candidates'][0]['content']['parts'][0]['text']
        
        # Limpieza
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

# --- 4. PUBLICAR ---
def publish(article):
    if not article:
        print("❌ No hay artículo para publicar.")
        sys.exit(1)

    print(f"🚀 Publicando: {article['titulo']}")
    
    try:
        # FOTO ULTRA-REALISTA (Pollinations con modelo FLUX-REALISM)
        # Esto genera una foto que parece real basada en lo que dijo la IA
        prompt_foto = urllib.parse.quote(article['foto_prompt'])
        img_url = f"https://image.pollinations.ai/prompt/{prompt_foto}?width=800&height=450&nologo=true&model=flux-realism&seed={random.randint(0,1000)}"
        
        html = f"""
        <div style="font-family: 'Georgia', serif; font-size: 19px; line-height: 1.8; color:#222;">
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 25px;">
                <img border="0" src="{img_url}" style="width:100%; max-width:800px; border-radius:5px; box-shadow:0 4px 10px rgba(0,0,0,0.1);" alt="Imagen de la noticia"/>
            </div>
            {article['contenido']}
            <br><hr>
            <p style="font-size:12px; color:#666; text-align:center;">Radar Internacional © 2026 - Cobertura Global</p>
        </div>
        """
        
        body = {
            "kind": "blogger#post",
            "title": article["titulo"],
            "content": html,
            "labels": ["Internacional", "Noticias"]
        }
        
        service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print("✅ ¡EXITO TOTAL! Noticia publicada.")
        
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
