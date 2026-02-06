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
    2. **Imagen:** Dame un PROMPT EN INGLÉS para generar una foto realista (ej: "President giving speech, photorealistic").
    3. **Texto:** Usa negritas (<b>) para resaltar lo importante.
   
    FORMATO DE SALIDA (Usa separador ||||):
    TITULO||||KEYWORD_FOTO_INGLES||||CONTENIDO_HTML

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
                "foto_keyword": parts[1].strip(),
                "contenido": parts[2].strip()
            }
        else:
            return None 
    except Exception as e:
        print(f"⚠️ Error IA: {e}")
        return None
        
# --- 4. BUSCAR FOTO REAL EN PEXELS ---
def get_pexels_image(keyword):
    print(f"📸 Buscando foto real de: {keyword}...")
    try:
        url = f"https://api.pexels.com/v1/search?query={keyword}&per_page=1&orientation=landscape"
        headers = {'Authorization': PEXELS_KEY}
        
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if data['photos']:
            # Devolvemos la foto en tamaño grande (landscape)
            return data['photos'][0]['src']['landscape']
        else:
            # Si no encuentra, foto genérica de noticias
            return "https://images.pexels.com/photos/3944454/pexels-photo-3944454.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1"
    except Exception as e:
        print(f"⚠️ Error Pexels: {e}")
        return "https://images.pexels.com/photos/3944454/pexels-photo-3944454.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1"


# --- 4. PUBLICAR ---
def publish(article):
    if not article:
        print("❌ Error en generación.")
        sys.exit(1)

    print(f"🚀 Publicando: {article['titulo']}")
    
    try:
        # Obtenemos la foto real
        img_url = get_pexels_image(article['foto_keyword'])
        
        html = f"""
        <div style="font-family: 'Georgia', serif; font-size: 19px; line-height: 1.8; color:#111;">
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 25px;">
                <img border="0" src="{img_url}" style="width:100%; max-width:800px; border-radius:5px;" alt="Imagen de actualidad"/>
                <br/><small style="font-family:Arial; font-size:10px; color:#666;">FOTO: AGENCIA (Pexels)</small>
            </div>
            {article['contenido']}
            <br><hr>
            <p style="font-size:12px; color:#666;">Radar Internacional © 2026</p>
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
