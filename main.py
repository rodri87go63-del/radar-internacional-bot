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

print("📰 INICIANDO REDACCIÓN PROFESIONAL (RADAR)...")

# --- 1. CONFIGURACIÓN ---
RSS_URLS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.rt.com/rss/news/"
]

try:
    token_info = json.loads(os.environ["GOOGLE_TOKEN"])
    creds = Credentials.from_authorized_user_info(token_info)
    service = build('blogger', 'v3', credentials=creds)
    BLOG_ID = os.environ["BLOG_ID"]
    
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"❌ Error de configuración: {e}")
    sys.exit(1)

# --- 2. OBTENER INFORMACIÓN ---
def get_latest_news():
    print("📡 Recopilando cables de agencias...")
    news_text = ""
    count = 0
    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]: # Leemos 3 de cada medio
                count += 1
                # Limpiamos el texto para que la IA entienda mejor
                clean_title = entry.title.replace('"', "'")
                news_text += f"Noticia {count}: {clean_title}\n"
        except:
            pass
    return news_text

# --- 3. CEREBRO IA (Redacción y Selección de Imagen) ---
def generate_article(raw_data):
    print("🧠 Analizando, Traduciendo y Redactando...")
    
    prompt = f"""
    Actúa como el Editor Jefe de 'Radar Internacional', un diario digital serio en español.
    
    TUS FUENTES DE HOY (En inglés):
    {raw_data}

    TU TAREA:
    1. Elige la noticia MÁS IMPORTANTE de la lista.
    2. TRADUCE Y REDACTA una noticia completa en ESPAÑOL NEUTRO.
    3. El tono debe ser formal, periodístico y objetivo.
    4. Genera palabras clave en INGLÉS para buscar una foto real relacionada.

    FORMATO DE RESPUESTA (JSON PURO, SIN MARKDOWN):
    {{
        "titulo": "ESCRIBE AQUÍ UN TITULO PERIODÍSTICO EN ESPAÑOL",
        "contenido": "CÓDIGO HTML DEL CUERPO",
        "keywords_imagen": "keyword1,keyword2" 
    }}

    REGLAS DEL HTML (contenido):
    - Usa <p> para párrafos.
    - Usa <b>CIUDAD (Radar) —</b> al inicio del primer párrafo.
    - Usa un <h2> a la mitad para un subtítulo.
    - NO uses H1. NO pongas el título dentro del contenido.
    - El texto debe ser extenso (mínimo 4 párrafos).
    """
    
    try:
        response = model.generate_content(prompt)
        # Limpieza quirúrgica del JSON
        txt = response.text
        # Borrar ```json y ``` si existen
        txt = re.sub(r'```json', '', txt)
        txt = re.sub(r'```', '', txt)
        txt = txt.strip()
        
        return json.loads(txt)
    except Exception as e:
        print(f"⚠️ Error IA: {e}")
        print("Reintentando formato simple...")
        return None

# --- 4. PUBLICAR ---
def publish(article):
    if not article:
        print("❌ No se pudo generar el artículo.")
        return

    print(f"🚀 Publicando: {article['titulo']}")
    
    try:
        # BÚSQUEDA DE FOTO REAL RELACIONADA
        # Usamos las keywords que la IA eligió (ej: "Biden, Congress" o "War, Tank")
        # LoremFlickr busca en Flickr fotos reales con esos tags.
        search_terms = article['keywords_imagen'].replace(" ", "").replace(",", ",")
        ts = int(time.time())
        img_url = f"https://loremflickr.com/800/450/{search_terms}/all?lock={ts}"
        
        # HTML PROFESIONAL
        html_content = f"""
        <div style="font-family: Georgia, serif; font-size: 18px; line-height: 1.6; color: #333;">
            
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 25px;">
                <img border="0" src="{img_url}" style="width: 100%; max-width: 800px; border-radius: 4px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);" alt="Imagen de actualidad" />
                <br/>
                <small style="color: #666; font-family: Arial, sans-serif; font-size: 11px; text-transform: uppercase;">
                    Imagen Referencial de Archivo: {article['keywords_imagen']}
                </small>
            </div>

            {article['contenido']}

            <div style="margin-top: 30px; padding: 15px; background-color: #f9f9f9; border-top: 2px solid #D90000;">
                <p style="font-family: Arial, sans-serif; font-size: 12px; color: #555; margin: 0;">
                    <b>RADAR INTERNACIONAL</b><br>
                    Cobertura automatizada de fuentes globales (BBC, NYT, RT).<br>
                    <i>Redacción asistida por Inteligencia Artificial.</i>
                </p>
            </div>
        </div>
        """
        
        body = {
            "kind": "blogger#post",
            "title": article["titulo"],
            "content": html_content,
            "labels": ["Mundo", "Internacional", "Noticias"]
        }
        
        service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print("✅ ¡NOTICIA PUBLICADA CON ÉXITO!")
        
    except Exception as e:
        print(f"❌ Error al subir a Blogger: {e}")

if __name__ == "__main__":
    raw_news = get_latest_news()
    if len(raw_news) > 10:
        art = generate_article(raw_news)
        publish(art)
    else:
        print("❌ Error leyendo fuentes RSS")
