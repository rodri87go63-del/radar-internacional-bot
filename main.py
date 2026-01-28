import feedparser
import google.generativeai as genai
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
import json
import random
import time
import sys
import urllib.request

print("📰 INICIANDO RADAR (MODELO COMPATIBLE)...")

# --- 1. FUENTES ---
RSS_URLS = [
    "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada",
    "https://www.bbc.com/mundo/temas/internacional/index.xml"
]

try:
    token_info = json.loads(os.environ["GOOGLE_TOKEN"])
    creds = Credentials.from_authorized_user_info(token_info)
    service = build('blogger', 'v3', credentials=creds)
    BLOG_ID = os.environ["BLOG_ID"]
    
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    # CAMBIO CLAVE: Usamos 'gemini-pro' que es más estable
    model = genai.GenerativeModel('gemini-pro')
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
            
            for entry in feed.entries[:5]:
                if hasattr(entry, 'summary'):
                    candidates.append(f"TITULAR: {entry.title}\nRESUMEN: {entry.summary}")
        except:
            pass
            
    if not candidates:
        return None
    
    return random.choice(candidates)

# --- 3. REDACCIÓN ---
def write_full_article(story_data):
    print("🧠 IA: Redactando...")
    
    prompt = f"""
    Eres Periodista de 'Radar Internacional'.
    
    FUENTE:
    {story_data}

    TAREA:
    Escribe un ARTÍCULO DE 4 PÁRRAFOS en ESPAÑOL NEUTRO.
    
    REGLAS:
    1. Título periodístico real (Sin números).
    2. Usa negritas (<b>) para resaltar datos.
    3. Dame 1 palabra clave en INGLÉS para la foto.
    
    FORMATO DE SALIDA (Usa el separador ||||):
    TITULO||||KEYWORD_FOTO||||CONTENIDO_HTML
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```", "").replace("html", "").strip()
        parts = text.split("||||")
        
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

# --- 4. PUBLICAR ---
def publish(article):
    if not article:
        print("❌ Error en generación.")
        return

    print(f"🚀 Publicando: {article['titulo']}")
    
    try:
        tag = article['foto_keyword'].replace(" ", "")
        ts = int(time.time())
        img_url = f"https://loremflickr.com/800/500/{tag}/all?lock={ts}"
        
        html = f"""
        <div style="font-family: 'Georgia', serif; font-size: 18px; line-height: 1.8;">
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 25px;">
                <img border="0" src="{img_url}" style="width:100%; max-width:800px; border-radius:5px;" alt="{tag}"/>
            </div>
            {article['contenido']}
            <br><hr><i>Radar Internacional</i>
        </div>
        """
        
        body = {
            "kind": "blogger#post",
            "title": article["titulo"],
            "content": html,
            "labels": ["Internacional"]
        }
        
        service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print("✅ ¡EXITO!")
        
    except Exception as e:
        print(f"❌ Error publicando: {e}")
        sys.exit(1)

if __name__ == "__main__":
    story = get_one_story()
    if story:
        art = write_full_article(story)
        publish(art)
    else:
        print("❌ Sin noticias.")
        sys.exit(1)
