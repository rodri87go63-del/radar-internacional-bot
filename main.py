import feedparser
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
import json
import random
import time
import sys
import urllib.request
import requests 

print("🚀 INICIANDO RADAR (MODELO FLASH 1.5 - MÉTODO DIRECTO)...")

# --- 1. CONFIGURACIÓN ---
RSS_URLS = [
    "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada",
    "https://www.bbc.com/mundo/temas/internacional/index.xml"
]

try:
    # 1. Configurar Blogger
    token_info = json.loads(os.environ["GOOGLE_TOKEN"])
    creds = Credentials.from_authorized_user_info(token_info)
    service = build('blogger', 'v3', credentials=creds)
    BLOG_ID = os.environ["BLOG_ID"]
    
    # 2. URL DIRECTA A LA IA (GEMINI 1.5 FLASH)
    # Esta es la dirección exacta que funciona hoy.
    API_KEY = os.environ["GEMINI_API_KEY"]
    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
    print("✅ Credenciales OK.")
except Exception as e:
    print(f"❌ Error Config: {e}")
    sys.exit(1)

# --- 2. SELECCIONAR UNA NOTICIA ---
def get_one_story():
    print("📡 Buscando noticia...")
    candidates = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for url in RSS_URLS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                feed = feedparser.parse(response.read())
            
            # Filtramos noticias con contenido
            for entry in feed.entries[:5]:
                summary = entry.summary if hasattr(entry, 'summary') else entry.title
                if len(summary) > 20:
                    candidates.append(f"TITULAR: {entry.title}\nRESUMEN: {summary}")
        except:
            pass
            
    if not candidates:
        print("⚠️ No hay noticias RSS disponibles.")
        return None
    
    # Elegimos una al azar
    return random.choice(candidates)

# --- 3. REDACCIÓN (CONEXIÓN DIRECTA) ---
def write_full_article(story_data):
    print("🧠 IA: Redactando reportaje extenso...")
    
    prompt = f"""
    Eres un Reportero Senior de 'Radar Internacional'.
    
    FUENTE DE LA NOTICIA:
    {story_data}

    TU TAREA:
    Escribe un ARTÍCULO COMPLETO Y LARGO en ESPAÑOL NEUTRO.
    No hagas un resumen. Desarrolla la noticia explicando el contexto, antecedentes y qué significa esto para el mundo.

    REQUISITOS OBLIGATORIOS:
    1. **TÍTULO:** Un titular periodístico real y serio (Sin números, sin "Informe").
    2. **CONTENIDO:** Mínimo 4 párrafos largos.
    3. **FOTO:** Dame 1 sola palabra clave en INGLÉS que describa el SUJETO PRINCIPAL (ej: "Biden", "Ukraine", "Oil", "Protest"). Debe ser algo concreto para buscar la foto.
    
    FORMATO DE SALIDA (Usa el separador ||||):
    TITULO||||KEYWORD_FOTO_INGLES||||CONTENIDO_HTML

    REGLAS HTML:
    - Primer párrafo empieza: <b>LONDRES/WASHINGTON (Radar) —</b> ...
    - Usa <p> para cada párrafo.
    - Usa <b>negritas</b> para nombres importantes.
    - NO uses Markdown.
    """
    
    # Empaquetamos el mensaje
    payload = { "contents": [{ "parts": [{"text": prompt}] }] }
    
    try:
        # Petición POST directa
        response = requests.post(API_URL, json=payload)
        
        if response.status_code != 200:
            print(f"❌ Error Google ({response.status_code}): {response.text}")
            return None
            
        result = response.json()
        texto = result['candidates'][0]['content']['parts'][0]['text']
        
        # Limpieza
        texto = texto.replace("```html", "").replace("```", "").strip()
        parts = texto.split("||||")
        
        if len(parts) >= 3:
            return {
                "titulo": parts[0].strip(),
                "foto_keyword": parts[1].strip(),
                "contenido": parts[2].strip()
            }
        else:
            print("⚠️ La IA no respetó el formato. Intentando reciclar texto...")
            # Si falla el formato, intentamos salvar el texto
            return {
                "titulo": "Actualidad Global: Informe Especial",
                "foto_keyword": "news",
                "contenido": f"<p>{texto}</p>"
            }
            
    except Exception as e:
        print(f"⚠️ Error IA: {e}")
        return None

# --- 4. PUBLICAR ---
def publish(article):
    if not article:
        print("❌ No hay artículo para publicar.")
        sys.exit(1)

    print(f"🚀 Publicando: {article['titulo']}")
    
    try:
        tag = article['foto_keyword'].replace(" ", "")
        ts = int(time.time())
        # Buscamos foto real en Flickr usando la palabra clave de la noticia
        img_url = f"https://loremflickr.com/800/500/{tag}/all?lock={ts}"
        
        html = f"""
        <div style="font-family: 'Georgia', serif; font-size: 19px; line-height: 1.8; color:#111;">
            
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 30px;">
                <img border="0" src="{img_url}" style="width:100%; max-width:800px; border-radius:4px; box-shadow:0 4px 8px rgba(0,0,0,0.1);" alt="Imagen: {tag}"/>
                <br/><small style="font-family:Arial; font-size:10px; color:#666; text-transform:uppercase;">ARCHIVO: {tag}</small>
            </div>

            {article['contenido']}

            <div style="margin-top:40px; padding-top:10px; border-top:1px solid #ccc;">
                <p style="font-family:Arial; font-size:12px; color:#888;">Radar Internacional - Cobertura Global</p>
            </div>
        </div>
        """
        
        body = {
            "kind": "blogger#post",
            "title": article["titulo"],
            "content": html,
            "labels": ["Internacional", "Noticias"]
        }
        
        service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print("✅ ¡EXITO TOTAL! Noticia publicada.")
        
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
