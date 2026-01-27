import feedparser
import google.generativeai as genai
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
import json
import random
import time
import sys
import re
import urllib.request

print("🚀 INICIANDO SISTEMA DE NOTICIAS 2.0...")

# --- 1. CONFIGURACIÓN ---
# Usamos URLs que suelen ser más permisivas
RSS_URLS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.rt.com/rss/news/",
    "https://rss.elpais.com/rss/internacional/portada.xml"
]

try:
    token_info = json.loads(os.environ["GOOGLE_TOKEN"])
    creds = Credentials.from_authorized_user_info(token_info)
    service = build('blogger', 'v3', credentials=creds)
    BLOG_ID = os.environ["BLOG_ID"]
    
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("✅ Credenciales configuradas correctamente.")
except Exception as e:
    print(f"❌ ERROR CRÍTICO DE CREDENCIALES: {e}")
    sys.exit(1)

# --- 2. OBTENER NOTICIAS (CON DISFRAZ) ---
def get_latest_news():
    print("📡 Conectando con agencias de noticias...")
    news_text = ""
    
    # Truco: Añadimos 'User-Agent' para no parecer un robot
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    for url in RSS_URLS:
        try:
            # Descargar el feed manualmente con el disfraz
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                xml_data = response.read()
                feed = feedparser.parse(xml_data)
                
            print(f"   - {url}: {len(feed.entries)} noticias encontradas.")
            
            for entry in feed.entries[:3]:
                title = entry.title
                news_text += f"- {title}\n"
        except Exception as e:
            print(f"   ⚠️ Error leyendo {url}: {e}")

    if len(news_text) < 10:
        print("❌ ALERTA: No se pudieron descargar noticias. Usando respaldo.")
        return "El panorama internacional se centra hoy en la economía global, tensiones geopolíticas en Europa y avances tecnológicos en inteligencia artificial."
    
    return news_text

# --- 3. REDACCIÓN INTELIGENTE (ESPAÑOL) ---
def generate_article(raw_data):
    print("🧠 IA Analizando y Redactando...")
    
    prompt = f"""
    Eres el Editor de 'Radar Internacional'.
    CABLES DE NOTICIAS:
    {raw_data}

    INSTRUCCIONES:
    1. Elige la noticia más relevante.
    2. Escribe un artículo en ESPAÑOL NEUTRO PERFECTO.
    3. Estilo: Periodístico, formal, serio.
    4. Define 2 palabras clave en INGLÉS para buscar la foto (ej: "Biden, Congress").

    FORMATO JSON OBLIGATORIO:
    {{
        "titulo": "TITULO EN ESPAÑOL AQUI",
        "contenido": "CONTENIDO HTML AQUI",
        "foto_keywords": "keyword1,keyword2"
    }}

    REGLAS HTML:
    - Inicia con: <b>LONDRES/NUEVA YORK (Radar) —</b>
    - Usa <p>, <h2> y <blockquote>.
    - Texto largo y detallado.
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"❌ Error IA: {e}")
        # Plan de emergencia si la IA falla
        ts = int(time.time())
        return {
            "titulo": f"Boletín Urgente Radar #{ts}",
            "contenido": f"<p><b>REDACCIÓN (Radar) —</b><br>Resumen de titulares procesados: {raw_data[:200]}...</p>",
            "foto_keywords": "news, paper"
        }

# --- 4. PUBLICAR CON FOTO REAL ---
def publish(article):
    print(f"🚀 Publicando: {article['titulo']}")
    try:
        # Búsqueda de foto real en Flickr (LoremFlickr)
        keywords = article.get("foto_keywords", "news").replace(" ", "").replace(",", ",")
        ts = int(time.time())
        # Filtramos por 'all' para tener más variedad
        img_url = f"https://loremflickr.com/800/450/{keywords}/all?lock={ts}"
        
        html = f"""
        <div style="font-family: Georgia, serif; color: #333; font-size: 18px; line-height: 1.6;">
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 20px;">
                <img border="0" src="{img_url}" style="width:100%; max-width:800px; border-radius:5px;" alt="Imagen de actualidad"/>
                <br/><small style="font-family:Arial; font-size:11px; color:#666;">Imagen referencial ({keywords})</small>
            </div>
            {article['contenido']}
            <br><hr>
            <p style="font-family:Arial; font-size:12px; color:#888; text-align:center;">
                Radar Internacional © 2025 - Cobertura Global
            </p>
        </div>
        """
        
        body = {
            "kind": "blogger#post",
            "title": article["titulo"],
            "content": html,
            "labels": ["Internacional", "Noticias", "Mundo"]
        }
        
        res = service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print(f"✅ ¡PUBLICADO CON ÉXITO! URL: {res.get('url')}")
        
    except Exception as e:
        print(f"❌ ERROR FINAL PUBLICANDO: {e}")
        sys.exit(1)

if __name__ == "__main__":
    datos = get_latest_news()
    art = generate_article(datos)
    publish(art)
