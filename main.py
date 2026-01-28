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
import urllib.parse

print("🚀 INICIANDO RADAR (MODO IA PÚBLICA SIN CLAVES)...")

# --- 1. CONFIGURACIÓN ---
RSS_URLS = [
    "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada",
    "https://www.bbc.com/mundo/temas/internacional/index.xml"
]

try:
    # Solo necesitamos credenciales de Blogger
    token_info = json.loads(os.environ["GOOGLE_TOKEN"])
    creds = Credentials.from_authorized_user_info(token_info)
    service = build('blogger', 'v3', credentials=creds)
    BLOG_ID = os.environ["BLOG_ID"]
    print("✅ Conexión Blogger OK.")
except Exception as e:
    print(f"❌ Error Credenciales Blogger: {e}")
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
            
            for entry in feed.entries[:5]:
                summary = entry.summary if hasattr(entry, 'summary') else entry.title
                if len(summary) > 20:
                    candidates.append(f"TITULAR: {entry.title}\nRESUMEN: {summary}")
        except:
            pass
            
    if not candidates:
        return None
    return random.choice(candidates)

# --- 3. REDACCIÓN (USANDO POLLINATIONS TEXT - SIN API KEY) ---
def write_full_article(story_data):
    print("🧠 IA: Redactando reportaje (Sistema Alternativo)...")
    
    # Instrucciones para la IA
    system_prompt = f"""
    Eres un Periodista Senior de 'Radar Internacional'.
    Escribe un ARTÍCULO DE FONDO (4 párrafos largos) en ESPAÑOL NEUTRO basado en:
    {story_data}
    
    FORMATO DE RESPUESTA OBLIGATORIO (Usa los separadores ||||):
    TITULO||||KEYWORD_FOTO_INGLES||||CONTENIDO_HTML

    REGLAS:
    1. Título serio y profesional.
    2. KEYWORD_FOTO: Una o dos palabras en inglés que describan la imagen (ej: "War", "Economy", "Trump").
    3. CONTENIDO: 4 párrafos HTML (<p>). Usa negritas (<b>) para datos clave.
    4. NO uses Markdown. Solo texto plano con los separadores.
    """
    
    try:
        # Llamada a la IA pública (No requiere clave)
        # Codificamos el prompt para enviarlo por URL
        prompt_safe = urllib.parse.quote(system_prompt)
        # Usamos un seed aleatorio para que varíe la creatividad
        seed = random.randint(1, 10000)
        url = f"https://text.pollinations.ai/{prompt_safe}?model=openai&seed={seed}"
        
        response = requests.get(url)
        
        if response.status_code != 200:
            print("Error en IA Pública.")
            return None
            
        texto = response.text
        
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
            print("⚠️ Formato incorrecto, intentando modo simple...")
            # Si el formato falla, usamos el texto completo como contenido
            return {
                "titulo": "Actualidad Global: Análisis",
                "foto_keyword": "news",
                "contenido": f"<p><b>REDACCIÓN (Radar) —</b> {texto}</p>"
            }
            
    except Exception as e:
        print(f"⚠️ Error IA: {e}")
        return None

# --- 4. PUBLICAR ---
def publish(article):
    if not article:
        print("❌ No se generó artículo.")
        sys.exit(1)

    print(f"🚀 Publicando: {article['titulo']}")
    
    try:
        tag = article['foto_keyword'].replace(" ", "")
        ts = int(time.time())
        img_url = f"https://loremflickr.com/800/500/{tag}/all?lock={ts}"
        
        html = f"""
        <div style="font-family: 'Georgia', serif; font-size: 19px; line-height: 1.8;">
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 25px;">
                <img border="0" src="{img_url}" style="width:100%; max-width:800px; border-radius:5px;" alt="{tag}"/>
                <br/><small style="font-family:Arial; font-size:10px; color:#666;">ARCHIVO: {tag.upper()}</small>
            </div>
            {article['contenido']}
            <br><hr>
            <p style="font-size:12px; color:#666;">Radar Internacional - Análisis y Cobertura</p>
        </div>
        """
        
        body = {
            "kind": "blogger#post",
            "title": article["titulo"],
            "content": html,
            "labels": ["Internacional", "Noticias"]
        }
        
        service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print("✅ ¡EXITO TOTAL! Noticia Publicada.")
        
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
