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

print("🚀 INICIANDO RADAR (SISTEMA DE FOTOS INTELIGENTES)...")

# --- 1. CONFIGURACIÓN ---
RSS_URLS = [
    "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada",
    "https://www.bbc.com/mundo/temas/internacional/index.xml"
]

try:
    token_info = json.loads(os.environ["GOOGLE_TOKEN"])
    creds = Credentials.from_authorized_user_info(token_info)
    service = build('blogger', 'v3', credentials=creds)
    BLOG_ID = os.environ["BLOG_ID"]
    print("✅ Conexión Blogger OK.")
except Exception as e:
    print(f"❌ Error Credenciales: {e}")
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
                    # Guardamos título y resumen para que la IA entienda de qué hablar
                    candidates.append(f"TITULAR: {entry.title}\nCONTEXTO: {summary}")
        except:
            pass
            
    if not candidates:
        return None
    return random.choice(candidates)

# --- 3. REDACCIÓN Y DESCRIPCIÓN DE IMAGEN ---
def write_full_article(story_data):
    print("🧠 IA: Redactando y diseñando imagen...")
    
    # Instrucciones precisas para la IA
    system_prompt = f"""
    Eres un Periodista Senior de 'Radar Internacional'.
    
    NOTICIA A CUBRIR:
    {story_data}

    TAREAS:
    1. Escribe un ARTÍCULO DE FONDO (4 párrafos) en ESPAÑOL NEUTRO.
    2. Crea una DESCRIPCIÓN VISUAL para la foto en INGLÉS.
       - MAL: "Politics"
       - BIEN: "Donald Trump speaking at a podium in the White House, realistic news photography, 4k"
       - BIEN: "Ruins of a building in Gaza after airstrike, smoke, realistic, journalism style"
    
    FORMATO DE RESPUESTA OBLIGATORIO (Separador ||||):
    TITULO_PROFESIONAL||||DESCRIPCION_VISUAL_EN_INGLES||||CONTENIDO_HTML

    REGLAS HTML:
    - Primer párrafo: <b>CIUDAD (Radar) —</b> ...
    - Usa <p> para párrafos.
    - No uses Markdown.
    """
    
    try:
        # Usamos Pollinations Text (Modelo OpenAI/GPT compatible)
        prompt_safe = urllib.parse.quote(system_prompt)
        seed = random.randint(1, 10000)
        # Forzamos modelo 'openai' o 'mistral' para mejor razonamiento
        url = f"https://text.pollinations.ai/{prompt_safe}?model=openai&seed={seed}"
        
        response = requests.get(url, timeout=60)
        texto = response.text
        
        # Limpieza
        texto = texto.replace("```html", "").replace("```", "").strip()
        parts = texto.split("||||")
        
        if len(parts) >= 3:
            return {
                "titulo": parts[0].strip(),
                "foto_prompt": parts[1].strip(),
                "contenido": parts[2].strip()
            }
        else:
            print("⚠️ Formato incorrecto de IA.")
            return None
            
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
        # GENERACIÓN DE IMAGEN REALISTA (MODELO FLUX)
        # Usamos la descripción detallada que nos dio la IA + filtros de realismo
        base_prompt = article['foto_prompt']
        # Añadimos "magic words" para forzar realismo
        full_prompt = f"{base_prompt}, news photography, 8k, highly detailed, realistic, press photo"
        
        prompt_encoded = urllib.parse.quote(full_prompt)
        img_url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=800&height=450&model=flux&nologo=true&seed={random.randint(1,999)}"
        
        html = f"""
        <div style="font-family: 'Georgia', serif; font-size: 19px; line-height: 1.8; color:#222;">
            
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 25px;">
                <img border="0" src="{img_url}" style="width:100%; max-width:800px; border-radius:5px;" alt="Imagen de la noticia"/>
                <br/><small style="font-family:Arial; font-size:10px; color:#666;">FOTOGRAFÍA DE ARCHIVO</small>
            </div>

            {article['contenido']}

            <div style="margin-top:30px; border-top:1px solid #ccc; padding-top:10px;">
                <p style="font-size:12px; color:#666; font-family:Arial;">Radar Internacional - Cobertura Global</p>
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
