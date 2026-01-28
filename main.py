import feedparser
from google import genai # <--- ESTA ES LA NUEVA LIBRERÍA
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
import json
import random
import time
import sys
import urllib.request

print("🚀 INICIANDO RADAR (LIBRERÍA OFICIAL GOOGLE.GENAI)...")

# --- 1. CONFIGURACIÓN ---
RSS_URLS = [
    "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada",
    "https://www.bbc.com/mundo/temas/internacional/index.xml"
]

try:
    # 1. Configurar Blogger (Esto no cambia)
    token_info = json.loads(os.environ["GOOGLE_TOKEN"])
    creds = Credentials.from_authorized_user_info(token_info)
    service = build('blogger', 'v3', credentials=creds)
    BLOG_ID = os.environ["BLOG_ID"]
    
    # 2. Configurar la NUEVA IA
    # Creamos el Cliente oficial
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    
    print("✅ Credenciales y Cliente IA cargados.")
except Exception as e:
    print(f"❌ Error Configuración: {e}")
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
            
            for entry in feed.entries[:6]:
                # Buscamos noticias con algo de contenido
                summary = entry.summary if hasattr(entry, 'summary') else entry.title
                if len(summary) > 20:
                    candidates.append(f"TITULAR: {entry.title}\nDATOS: {summary}")
        except:
            pass
            
    if not candidates:
        return None
    return random.choice(candidates)

# --- 3. REDACCIÓN (SINTAXIS NUEVA) ---
def write_full_article(story_data):
    print("🧠 IA: Redactando reportaje...")
    
    prompt = f"""
    Eres un Periodista Senior de 'Radar Internacional'.
    
    NOTICIA:
    {story_data}

    TAREA:
    Escribe un ARTÍCULO DE FONDO (4 párrafos) en ESPAÑOL NEUTRO.
    Extiende la información explicando el contexto y las consecuencias.
    
    REQUISITOS:
    1. Título profesional (sin números).
    2. 4 Párrafos bien estructurados.
    3. Una palabra clave en inglés para la foto.
    
    FORMATO DE SALIDA (Usa el separador ||||):
    TITULO||||KEYWORD_FOTO_INGLES||||CONTENIDO_HTML

    REGLAS HTML:
    - Primer párrafo: <b>CIUDAD (Radar) —</b> ...
    - Usa <p>, <b> y <blockquote>.
    - No uses Markdown.
    """
    
    try:
        # ASÍ SE LLAMA A LA IA CON LA LIBRERÍA NUEVA:
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        
        text = response.text.replace("```html", "").replace("```", "").strip()
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
        print("❌ Error: No se generó el artículo.")
        sys.exit(1)

    print(f"🚀 Publicando: {article['titulo']}")
    
    try:
        tag = article['foto_keyword'].replace(" ", "")
        ts = int(time.time())
        img_url = f"https://loremflickr.com/800/500/{tag}/all?lock={ts}"
        
        html = f"""
        <div style="font-family: 'Georgia', serif; font-size: 18px; line-height: 1.8;">
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 25px;">
                <img border="0" src="{img_url}" style="width:100%; max-width:800px; border-radius:5px;" alt="{tag}"/>
                <br/><small style="font-family:Arial; font-size:10px; color:#666;">ARCHIVO: {tag.upper()}</small>
            </div>
            {article['contenido']}
            <br><hr><i>Radar Internacional - Análisis Global</i>
        </div>
        """
        
        body = {
            "kind": "blogger#post",
            "title": article["titulo"],
            "content": html,
            "labels": ["Internacional", "Noticias"]
        }
        
        service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print("✅ ¡EXITO TOTAL!")
        
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
