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

print("🚀 INICIANDO RADAR INTERNACIONAL (VERSIÓN PRO)...")

# --- 1. CONFIGURACIÓN ---
# Fuentes fiables
RSS_URLS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
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
except Exception as e:
    print(f"❌ Error Credenciales: {e}")
    sys.exit(1)

# --- 2. LECTURA DE NOTICIAS (CON DISFRAZ) ---
def get_latest_news():
    print("📡 Escaneando el mundo...")
    news_text = ""
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for url in RSS_URLS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                feed = feedparser.parse(response.read())
            
            # Tomamos 2 noticias de cada medio para tener variedad
            for entry in feed.entries[:2]:
                news_text += f"- {entry.title}\n"
        except:
            pass
            
    if len(news_text) < 10:
        return "Crisis económica global y tensiones políticas en aumento."
    return news_text

# --- 3. FUNCIÓN DE LIMPIEZA (EL CIRUJANO) ---
def limpiar_json(texto_sucio):
    # Esta función busca donde empieza '{' y donde termina '}'
    try:
        inicio = texto_sucio.find('{')
        fin = texto_sucio.rfind('}') + 1
        if inicio != -1 and fin != 0:
            json_str = texto_sucio[inicio:fin]
            return json.loads(json_str)
        else:
            return None
    except:
        return None

# --- 4. CEREBRO IA (FUERZA BRUTA EN ESPAÑOL) ---
def generate_article(raw_data):
    print("🧠 IA: Escribiendo noticia en Español...")
    
    prompt = f"""
    Eres un periodista senior de 'Radar Internacional'.
    CABLES RECIBIDOS (Inglés/Español):
    {raw_data}

    TU MISIÓN:
    1. Selecciona la noticia más importante.
    2. TRADUCE Y REDACTA un artículo completo en ESPAÑOL NEUTRO.
    3. NO inventes noticias, usa los datos.
    4. Selecciona 2 palabras clave en INGLÉS para la foto (ej: "War, Tank" o "Meeting, Politician").

    FORMATO JSON OBLIGATORIO:
    {{
        "titulo": "TITULO IMPACTANTE EN ESPAÑOL",
        "contenido": "CODIGO HTML AQUI",
        "keywords_foto": "keyword1,keyword2"
    }}

    REGLAS HTML:
    - Primer párrafo empieza con: <b>LONDRES/NUEVA YORK (Radar) —</b>
    - Usa párrafos <p>, subtítulos <h2> y citas <blockquote>.
    - Mínimo 300 palabras.
    """
    
    try:
        response = model.generate_content(prompt)
        # Usamos el cirujano para extraer el JSON limpio
        datos = limpiar_json(response.text)
        
        if datos:
            return datos
        else:
            raise Exception("La IA no devolvió JSON válido")
            
    except Exception as e:
        print(f"⚠️ Error IA: {e}")
        # Plan C: Si falla, devolvemos esto para no quedarnos en blanco
        return {
            "titulo": "Actualidad Global: Resumen del Día",
            "contenido": f"<p><b>REDACCIÓN (Radar) —</b> Se están procesando múltiples reportes internacionales. Titulares destacados:<br><br>{raw_data[:400]}...</p>",
            "keywords_foto": "news, newspaper"
        }

# --- 5. PUBLICAR ---
def publish(article):
    print(f"🚀 Publicando: {article['titulo']}")
    
    try:
        # FOTOS REALES (LoremFlickr)
        # Limpiamos las keywords para que la URL sea válida
        tags = article.get("keywords_foto", "news").replace(" ", "").strip()
        ts = int(time.time())
        img_url = f"https://loremflickr.com/800/450/{tags}/all?lock={ts}"
        
        html = f"""
        <div style="font-family: Georgia, serif; font-size: 18px; color: #222; line-height: 1.6;">
            
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 25px;">
                <img border="0" src="{img_url}" style="width:100%; max-width:800px; border-radius:5px; box-shadow:0 2px 8px rgba(0,0,0,0.1);" alt="Imagen de la noticia"/>
                <br/><small style="font-family:Arial,sans-serif; font-size:11px; color:#777;">Imagen referencial: {tags}</small>
            </div>

            {article['contenido']}

            <div style="margin-top:40px; padding-top:20px; border-top:1px solid #ddd; text-align:center; font-family:Arial,sans-serif; font-size:12px; color:#888;">
                Radar Internacional © 2025<br>Cobertura automatizada de fuentes globales.
            </div>
        </div>
        """
        
        body = {
            "kind": "blogger#post",
            "title": article["titulo"],
            "content": html,
            "labels": ["Internacional", "Noticias", "Mundo"]
        }
        
        service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print("✅ ¡EXITO! Noticia publicada.")
        
    except Exception as e:
        print(f"❌ Error publicando: {e}")
        sys.exit(1)

if __name__ == "__main__":
    datos = get_latest_news()
    art = generate_article(datos)
    publish(art)
