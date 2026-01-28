import feedparser
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
import json
import random
import time
import sys
import urllib.request
import requests # Usamos esto para hablar directo con Google

print("🚀 INICIANDO RADAR INTERNACIONAL (CONEXIÓN DIRECTA)...")

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
    
    # 2. Configurar IA (Modo Directo)
    API_KEY = os.environ["GEMINI_API_KEY"]
    # Usamos la URL directa de la API, esto evita errores de librería
    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
    print("✅ Credenciales OK.")
except Exception as e:
    print(f"❌ Error Config: {e}")
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

# --- 3. REDACCIÓN (PETICIÓN DIRECTA) ---
def write_full_article(story_data):
    print("🧠 IA: Redactando vía API Directa...")
    
    prompt = f"""
    Eres un Periodista Senior de 'Radar Internacional'.
    
    NOTICIA BASE:
    {story_data}

    TU TAREA:
    Escribe un REPORTAJE EXTENSO (Mínimo 500 palabras) en ESPAÑOL NEUTRO.
    Expande la información explicando antecedentes, contexto y consecuencias.
    
    FORMATO DE SALIDA (Usa el separador ||||):
    TITULO||||KEYWORD_FOTO_INGLES||||CONTENIDO_HTML

    REGLAS HTML:
    - Usa párrafos <p> muy largos.
    - Usa subtítulos <h3>.
    - Usa negritas <b> para resaltar datos.
    - NO uses Markdown.
    """
    
    # Preparamos el paquete para enviar a Google
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        # Enviamos la carta directamente al servidor de Google
        response = requests.post(API_URL, json=payload)
        result = response.json()
        
        # Leemos la respuesta
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
            print("⚠️ Formato incorrecto de la IA.")
            return None 
            
    except Exception as e:
        print(f"⚠️ Error Conexión IA: {e}")
        # Si quieres ver el error real, descomenta la siguiente linea:
        # print(response.text)
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
        img_url = f"https://loremflickr.com/800/500/{tag}/all?lock={ts}"
        
        html = f"""
        <div style="font-family: 'Georgia', serif; font-size: 18px; line-height: 1.8;">
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 25px;">
                <img border="0" src="{img_url}" style="width:100%; max-width:800px; border-radius:5px;" alt="{tag}"/>
            </div>
            {article['contenido']}
            <br><hr><i>Radar Internacional</i>
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
