import feedparser
import google.generativeai as genai
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
import json
import random
import time

# --- 1. CONFIGURACIÓN ---
RSS_URLS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.rt.com/rss/news/",
    "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada"
]

# Configuración de claves
try:
    GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
    BLOG_ID = os.environ["BLOG_ID"]
    token_info = json.loads(os.environ["GOOGLE_TOKEN"])
    
    # Autenticación Google (Tu llave maestra)
    creds = Credentials.from_authorized_user_info(token_info)
    service = build('blogger', 'v3', credentials=creds)
    
    # Autenticación IA
    genai.configure(api_key=GEMINI_API_KEY)
    # Usamos el modelo Flash 1.5 que es el mejor para noticias rápidas
    model = genai.GenerativeModel('gemini-1.5-flash')

except Exception as e:
    print(f"Error de configuración: {e}")
    exit(1)

# --- 2. FUNCIONES ---
def get_latest_news():
    news_pool = []
    print("📡 Radar activado: Escaneando fuentes globales...")
    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]: 
                news_pool.append(f"- {entry.title}: {entry.summary}")
        except:
            pass
    random.shuffle(news_pool)
    return "\n".join(news_pool[:10]) 

def generate_article(raw_data):
    print("🧠 Procesando inteligencia artificial...")
    
    prompt = f"""
    Eres el Editor Jefe de 'Radar Internacional'.
    Cables recibidos:
    {raw_data}

    TAREA:
    1. Selecciona la noticia más importante.
    2. Escribe un artículo urgente y profesional en Español Neutro.
    3. Estilo: CNN/BBC.
    
    FORMATO DE SALIDA (JSON ÚNICO):
    {{
        "titulo": "TITULO CLICKBAIT PERO SERIO",
        "contenido": "CÓDIGO HTML AQUÍ",
        "etiquetas": ["Internacional", "Urgente", "Noticia"]
    }}
    
    REGLAS HTML:
    - Inicia con: <b>LONDRES/WASHINGTON (Radar) —</b>
    - Usa párrafos <p>, subtítulos <h2> y citas <blockquote>.
    - NO uses <h1> ni pongas el título en el contenido.
    """
    
    try:
        response = model.generate_content(prompt)
        text_clean = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text_clean)
    except Exception as e:
        print(f"❌ Error IA: {e}")
        return None

def publish_to_blogger(article):
    try:
        # Imagen HD aleatoria
        keywords = ["breaking news", "world", "press conference", "interview"]
        kw = random.choice(keywords)
        ts = int(time.time())
        img_url = f"https://source.unsplash.com/800x400/?{kw}&t={ts}"
        
        # HTML Final con imagen y pie de página
        image_html = f'<div class="separator" style="clear: both; text-align: center; margin-bottom:20px;"><img border="0" src="{img_url}" style="width:100%; border-radius:8px;" /></div>'
        footer_html = "<br><hr><p style='font-size:12px; color:#666; text-align:center;'><i>Radar Internacional © 2025 - Inteligencia Artificial</i></p>"
        
        final_content = image_html + article["contenido"] + footer_html
        
        body = {
            "kind": "blogger#post",
            "title": article["titulo"],
            "content": final_content,
            "labels": article.get("etiquetas", ["Noticias"])
        }
        
        # PUBLICAR (isDraft=False para que salga ya)
        service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print(f"✅ ¡PUBLICADO!: {article['titulo']}")
        return True
    except Exception as e:
        print(f"❌ Error Blogger: {e}")
        return False

# --- 3. EJECUCIÓN ---
if __name__ == "__main__":
    data = get_latest_news()
    if data:
        art = generate_article(data)
        if art:
            publish_to_blogger(art)
    else:
        print("Sin noticias nuevas.")
