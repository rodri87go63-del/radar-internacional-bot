import feedparser
import google.generativeai as genai
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
import json
import random
import time
import sys

print("🚀 INICIANDO RADAR INTERNACIONAL...")

# --- 1. CONFIGURACIÓN ---
RSS_URLS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.rt.com/rss/news/"
]

try:
    # Cargar credenciales
    token_info = json.loads(os.environ["GOOGLE_TOKEN"])
    creds = Credentials.from_authorized_user_info(token_info)
    service = build('blogger', 'v3', credentials=creds)
    BLOG_ID = os.environ["BLOG_ID"]
    
    # Configurar IA (Usamos el modelo FLASH que es el actual)
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("✅ Credenciales OK.")
except Exception as e:
    print(f"❌ ERROR CONFIGURACIÓN: {e}")
    sys.exit(1)

# --- 2. OBTENER NOTICIAS ---
def get_latest_news():
    print("📡 Leyendo noticias...")
    news_pool = []
    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                news_pool.append(f"- {entry.title}")
        except:
            pass
            
    if not news_pool:
        return "Noticia de última hora: Mercados globales atentos a cambios tecnológicos."
    
    return "\n".join(news_pool[:10])

# --- 3. GENERAR ARTÍCULO ---
def generate_article(raw_data):
    print("🧠 IA Trabajando...")
    
    prompt = f"""
    Actúa como 'Radar Internacional'. Escribe una noticia en HTML basada en esto:
    {raw_data}
    
    FORMATO JSON OBLIGATORIO:
    {{
        "titulo": "TITULO DE LA NOTICIA",
        "contenido": "<p><b>LONDRES (Radar) —</b> Texto de la noticia...</p>",
        "etiquetas": ["Mundo"]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        # Limpieza
        texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(texto_limpio)
        
    except Exception as e:
        print(f"⚠️ Error IA: {e}")
        print("⚠️ Activando PLAN DE EMERGENCIA (Texto simple)...")
        
        # PLAN B MANUAL (Esto nunca falla)
        ts = int(time.time())
        return {
            "titulo": f"Reporte Global Radar #{ts}",
            "contenido": f"<p><b>REDACCIÓN CENTRAL (Radar) —</b><br>Nuestros sistemas han detectado actividad noticiosa global. Se están procesando los datos de: {raw_data[:100]}...</p><p>Pronto más información.</p>",
            "etiquetas": ["Flash", "Radar"]
        }

# --- 4. PUBLICAR ---
def publish(article):
    print(f"🚀 Intentando publicar: {article['titulo']}...")
    try:
        keywords = ["news", "technology", "world"]
        img = f"https://source.unsplash.com/800x400/?{random.choice(keywords)}&t={int(time.time())}"
        html_img = f'<div style="text-align:center"><img src="{img}" style="width:100%; border-radius:8px;"/></div><br/>'
        
        body = {
            "kind": "blogger#post",
            "title": article["titulo"],
            "content": html_img + article["contenido"] + "<br><hr><i>Radar Internacional</i>",
            "labels": article.get("etiquetas", ["Noticias"])
        }
        
        # isDraft=False asegura que se publique PÚBLICAMENTE
        res = service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print(f"✅ ¡ÉXITO TOTAL! Ver noticia: {res.get('url')}")
    except Exception as e:
        print(f"❌ ERROR FINAL PUBLICANDO: {e}")
        sys.exit(1)

if __name__ == "__main__":
    datos = get_latest_news()
    art = generate_article(datos)
    publish(art)
