import feedparser
import google.generativeai as genai
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
import json
import random
import time
import sys

print("🔥 INICIANDO SISTEMA DE NOTICIAS (MODO ROBUSTO)...")

# --- 1. CONFIGURACIÓN ---
RSS_URLS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.rt.com/rss/news/",
    "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada"
]

try:
    token_info = json.loads(os.environ["GOOGLE_TOKEN"])
    creds = Credentials.from_authorized_user_info(token_info)
    service = build('blogger', 'v3', credentials=creds)
    BLOG_ID = os.environ["BLOG_ID"]
    
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    # Usamos Flash porque es el soportado actualmente
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"❌ Error Configuración: {e}")
    sys.exit(1)

# --- 2. OBTENER NOTICIAS REALES ---
def get_latest_news():
    print("📡 Buscando cables de noticias...")
    news_pool = []
    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:4]:
                news_pool.append(f"- {entry.title}")
        except:
            pass
    
    if not news_pool:
        # Si fallan los RSS, usamos un tema genérico para no detenernos
        return "Actualidad geopolítica mundial y mercados financieros."
        
    random.shuffle(news_pool)
    return "\n".join(news_pool[:12])

# --- 3. REDACCIÓN CON IA (CON RED DE SEGURIDAD) ---
def generate_article(raw_data):
    print("🧠 Redactando artículo...")
    
    prompt = f"""
    Eres 'Radar Internacional'. Escribe una noticia HTML basada en estos datos:
    {raw_data}
    
    OBLIGATORIO: Devuelve SOLO este formato JSON exacto:
    {{
        "titulo": "TITULO AQUÍ",
        "contenido": "CÓDIGO HTML AQUÍ (párrafos, h2, blockquote)",
        "etiquetas": ["Mundo", "Noticias"]
    }}
    
    REGLAS HTML:
    - Inicia: <b>LONDRES/WASHINGTON (Radar) —</b>
    - Estilo: Serio, BBC/CNN.
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"⚠️ La IA falló el formato JSON: {e}")
        print("⚠️ Activando Plan de Emergencia (Texto simple)...")
        
        # PLAN B: Si la IA falla, creamos un artículo manual con lo que haya
        ts = int(time.time())
        return {
            "titulo": f"Resumen Global de Noticias #{ts}",
            "contenido": f"<p><b>REDACCIÓN CENTRAL (Radar) —</b><br>Informe de última hora. Se reportan los siguientes titulares internacionales:</p><pre>{raw_data[:500]}...</pre><p>Ampliación en breve.</p>",
            "etiquetas": ["Flash", "Urgente"]
        }

# --- 4. PUBLICAR CON FOTO REAL (NO IA) ---
def publish(article):
    print(f"🚀 Preparando publicación: {article['titulo']}")
    
    try:
        # FOTOS REALES (LoremFlickr busca en Flickr Creative Commons)
        # Usamos timestamp para que la foto cambie siempre
        ts = int(time.time())
        keywords = "news,press,conference,politics,world"
        img_url = f"https://loremflickr.com/800/450/{keywords}?lock={ts}"
        
        html_content = f"""
        <div class="separator" style="clear: both; text-align: center; margin-bottom: 20px;">
            <img border="0" src="{img_url}" style="width: 100%; max-width: 800px; border-radius: 6px;" alt="Imagen referencial de noticias" />
            <br/><small style="color:#777; font-size:10px;">Imagen referencial de archivo (Stock)</small>
        </div>
        {article['contenido']}
        <br><hr>
        <p style="text-align:center; font-size:12px; color:#999;">
            <i>Radar Internacional - Cobertura Global Automatizada</i>
        </p>
        """
        
        body = {
            "kind": "blogger#post",
            "title": article["titulo"],
            "content": html_content,
            "labels": article.get("etiquetas", ["Noticias"])
        }
        
        # isDraft=False asegura que se publique YA
        service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print("✅ ¡PUBLICACIÓN EXITOSA! Revisa tu blog.")
        
    except Exception as e:
        print(f"❌ ERROR PUBLICANDO: {e}")
        sys.exit(1)

if __name__ == "__main__":
    noticias = get_latest_news()
    articulo = generate_article(noticias)
    publish(articulo)
