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

print("📰 INICIANDO EDICIÓN CENTRAL (FUENTES EN ESPAÑOL)...")

# --- 1. CONFIGURACIÓN (FUENTES 100% ESPAÑOL) ---
RSS_URLS = [
    "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada",
    "https://www.bbc.com/mundo/temas/internacional/index.xml",
    "https://rss.dw.com/xml/rss-sp-all"
]

try:
    token_info = json.loads(os.environ["GOOGLE_TOKEN"])
    creds = Credentials.from_authorized_user_info(token_info)
    service = build('blogger', 'v3', credentials=creds)
    BLOG_ID = os.environ["BLOG_ID"]
    
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"❌ Error Config: {e}")
    sys.exit(1)

# --- 2. OBTENER NOTICIAS (YA EN ESPAÑOL) ---
def get_latest_news():
    print("📡 Conectando con agencias hispanas...")
    news_text = ""
    # Disfraz para que no nos bloqueen
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    for url in RSS_URLS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                feed = feedparser.parse(response.read())
            
            # Recopilamos más contexto (Titulo + Resumen)
            for entry in feed.entries[:3]:
                desc = entry.summary if 'summary' in entry else ""
                news_text += f"TITULAR: {entry.title}\nCONTEXTO: {desc}\n\n"
        except:
            pass
            
    if len(news_text) < 50:
        return "Crisis en mercados globales y tensiones diplomáticas en aumento."
    return news_text

# --- 3. REDACCIÓN EXTENSA (FORMATO ROBUSTO) ---
def generate_article(raw_data):
    print("🧠 IA: Redactando análisis profundo...")
    
    # EL SECRETO: Usamos separadores ||| en lugar de JSON complejo
    prompt = f"""
    Eres un Periodista de Investigación Senior de 'Radar Internacional'.
    
    INFORMACIÓN DISPONIBLE:
    {raw_data}

    TU TAREA:
    1. Identifica el conflicto o evento más grave de la lista.
    2. Escribe un ARTÍCULO DE FONDO (Extenso, serio, profesional).
    3. NO uses saludos ni explicaciones.
    4. El idioma debe ser ESPAÑOL NEUTRO.

    ESTRUCTURA DE RESPUESTA OBLIGATORIA (Usa los separadores |||):
    TITULO DEL ARTÍCULO|||CONTENIDO HTML|||KEYWORDS_EN_INGLES

    DETALLES DEL CONTENIDO HTML:
    - Empieza con: <p><b>REDACCIÓN CENTRAL (Radar) —</b> ...</p>
    - Mínimo 400 palabras.
    - Usa subtítulos <h3> para separar secciones.
    - Usa un tono analítico (explica las causas y consecuencias).
    - Cierra con una conclusión.
    """
    
    try:
        response = model.generate_content(prompt)
        texto = response.text.strip()
        
        # Separamos las partes usando el separador mágico
        partes = texto.split("|||")
        
        if len(partes) >= 3:
            return {
                "titulo": partes[0].strip(),
                "contenido": partes[1].strip().replace("```html", "").replace("```", ""),
                "keywords": partes[2].strip()
            }
        else:
            raise Exception("Formato de respuesta incorrecto")
            
    except Exception as e:
        print(f"⚠️ Error IA: {e}")
        # Plan de Respaldo MEJORADO (Ya está en español)
        ts = int(time.time())
        return {
            "titulo": f"Informe de Actualidad Global #{ts}",
            "contenido": f"<p><b>REDACCIÓN (Radar) —</b><br>Nuestros corresponsales informan los siguientes titulares destacados del día:</p><pre style='white-space: pre-wrap;'>{raw_data[:800]}...</pre><p>Se está ampliando la información de estos sucesos.</p>",
            "keywords": "news, world"
        }

# --- 4. PUBLICAR ---
def publish(article):
    print(f"🚀 Publicando: {article['titulo']}")
    
    try:
        # Foto Real
        tags = article['keywords'].replace(" ", "").replace("\n", "")
        ts = int(time.time())
        # Buscamos en LoremFlickr
        img_url = f"https://loremflickr.com/800/450/{tags}/all?lock={ts}"
        
        html = f"""
        <div style="font-family: 'Georgia', serif; font-size: 19px; color: #1a1a1a; line-height: 1.8;">
            
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 30px;">
                <img border="0" src="{img_url}" style="width:100%; max-width:800px; border-radius:3px;" alt="Imagen de actualidad"/>
                <br/><small style="font-family:Arial; font-size:10px; color:#666; text-transform:uppercase; letter-spacing:1px;">Fotografía de Archivo: {tags}</small>
            </div>

            {article['contenido']}

            <div style="margin-top:50px; padding:20px; background:#f4f4f4; border-left:5px solid #000;">
                <p style="font-family:Arial,sans-serif; font-size:14px; color:#444; margin:0;">
                    <b>RADAR INTERNACIONAL</b><br>
                    <i>Análisis independiente de fuentes globales (BBC Mundo, DW, El País).</i>
                </p>
            </div>
        </div>
        """
        
        body = {
            "kind": "blogger#post",
            "title": article["titulo"],
            "content": html,
            "labels": ["Internacional", "Portada", "Mundo"]
        }
        
        service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print("✅ ¡NOTICIA PUBLICADA!")
        
    except Exception as e:
        print(f"❌ Error Publicando: {e}")
        sys.exit(1)

if __name__ == "__main__":
    datos = get_latest_news()
    art = generate_article(datos)
    publish(art)
