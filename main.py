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
    
    # ---------------------------------------------------------
    # ZONA DE INSTRUCCIONES (PROMPT) - ¡AQUÍ EDITAS TÚ!
    # ---------------------------------------------------------
    prompt = f"""
    Eres un Periodista de Investigación de 'Radar Internacional'.
    
    LA NOTICIA ES:
    {story_data}

    TU MISIÓN:
    Escribe un ARTÍCULO DE FONDO (Mínimo 4 párrafos largos) en ESPAÑOL NEUTRO.
    No hagas un resumen simple. Agrega contexto, antecedentes y análisis.

    REGLAS DE FORMATO:
    1. **Título:** Periodístico y serio.
    2. **Imagen:** Dame un PROMPT EN INGLÉS para generar una foto realista (ej: "President giving speech, photorealistic").
    3. **Texto:** Usa negritas (<b>) para resaltar lo importante.
    
    ESTRUCTURA DE RESPUESTA (Usa el separador ||||):
    TITULO||||PROMPT_FOTO_INGLES||||CONTENIDO_HTML_COMPLETO
    """
    # ---------------------------------------------------------
    
    payload = { "contents": [{ "parts": [{"text": prompt}] }] }
    
    try:
        response = requests.post(API_URL, json=payload)
        
        if response.status_code != 200:
            print(f"❌ Error Google: {response.text}")
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
            print("⚠️ La IA no respetó el separador ||||")
            return None 
            
    except Exception as e:
        print(f"⚠️ Error IA: {e}")
        return None

# --- 4. PUBLICAR ---
def publish(article):
    if not article:
        print("❌ No hay artículo.")
        sys.exit(1)

    print(f"🚀 Publicando: {article['titulo']}")
    
    try:
        # Generar foto con Pollinations usando la descripción de Gemini
        foto_desc = urllib.parse.quote(article['foto_prompt'])
        seed = random.randint(1, 9999)
        # Usamos modelo FLUX para máximo realismo
        img_url = f"https://image.pollinations.ai/prompt/{foto_desc}?width=800&height=450&model=flux&nologo=true&seed={seed}"
        
        html = f"""
        <div style="font-family: 'Georgia', serif; font-size: 19px; line-height: 1.8; color:#111;">
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 25px;">
                <img border="0" src="{img_url}" style="width:100%; max-width:800px; border-radius:5px;" alt="Imagen de la noticia"/>
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
