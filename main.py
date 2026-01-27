import feedparser
import google.generativeai as genai
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
import json
import random
import time

# --- 1. CONFIGURACIÓN DE FUENTES ---
RSS_URLS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.rt.com/rss/news/",
    "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada"
]

# --- 2. CONEXIÓN (Usando tus Secretos) ---
try:
    GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
    BLOG_ID = os.environ["BLOG_ID"]
    token_info = json.loads(os.environ["GOOGLE_TOKEN"])
    
    # Autenticación con Google
    creds = Credentials.from_authorized_user_info(token_info)
    
    # Autenticación con la IA
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    print(f"Error de configuración: {e}")
    exit()

# --- 3. FUNCIONES DEL ROBOT ---
def get_latest_news():
    news_pool = []
    print("📡 Radar activado: Escaneando fuentes...")
    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]: 
                news_pool.append(f"- {entry.title}: {entry.summary}")
        except:
            pass
    random.shuffle(news_pool)
    return "\n".join(news_pool[:8]) 

def generate_article(raw_data):
    print("🧠 Redactando noticia...")
    prompt = f"""
    Actúa como Editor de 'Radar Internacional'.
    Datos: {raw_data}
    
    Instrucciones:
    1. Escribe una noticia en HTML sobre el tema más importante.
    2. Usa <b>LONDRES/EEUU (Radar) —</b> al inicio.
    3. No uses markdown, solo JSON puro.
    
    FORMATO JSON OBLIGATORIO:
    {{
        "titulo": "TITULO DE LA NOTICIA",
        "contenido": "<p>Primer parrafo...</p><h2>Subtitulo</h2><p>Más texto...</p>",
        "etiquetas": ["Mundo", "Urgente"]
    }}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"Error IA: {e}")
        return None

def publish_to_blogger(article):
    try:
        service = build('blogger', 'v3', credentials=creds)
        
        # Imagen
        keywords = ["news", "world", "breaking"]
        kw = random.choice(keywords)
        img_url = f"https://source.unsplash.com/800x400/?{kw}&t={int(time.time())}"
        
        content = f'<div style="text-align:center"><img src="{img_url}" style="width:100%; border-radius:5px"/></div><br/>' + article["contenido"]
        
        body = {
            "kind": "blogger#post",
            "title": article["titulo"],
            "content": content,
            "labels": article["etiquetas"]
        }
        service.posts().insert(blogId=BLOG_ID, body=body).execute()
        print("✅ PUBLICADO EN EL BLOG")
    except Exception as e:
        print(f"Error publicando: {e}")

# --- 4. ARRANQUE ---
if __name__ == "__main__":
    print("--- INICIANDO ---")
    data = get_latest_news()
    if data:
        art = generate_article(data)
        if art:
            publish_to_blogger(art)
