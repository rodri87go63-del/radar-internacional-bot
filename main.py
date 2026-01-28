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

print("🚀 INICIANDO RADAR (MODO CAZADOR DE MODELOS)...")

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
    API_KEY = os.environ["GEMINI_API_KEY"]
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

# --- 3. REDACCIÓN (EL CAZADOR DE MODELOS) ---
def call_ai_hunter(prompt):
    # LISTA DE TODOS LOS MODELOS POSIBLES DE GOOGLE
    # El robot probará uno por uno hasta que funcione.
    posibles_modelos = [
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-pro",
        "gemini-1.0-pro"
    ]
    
    payload = { "contents": [{ "parts": [{"text": prompt}] }] }
    
    for modelo in posibles_modelos:
        print(f"🔫 Probando modelo: {modelo}...")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={API_KEY}"
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                print(f"✅ ¡CONECTADO CON {modelo}!")
                return response.json() # ÉXITO, devolvemos respuesta
            else:
                print(f"⚠️ {modelo} falló (Error {response.status_code}).")
        except Exception as e:
            print(f"⚠️ Error de red con {modelo}: {e}")
            
    print("❌ TODOS LOS MODELOS FALLARON. Revisa tu API KEY en Google AI Studio.")
    return None

def write_full_article(story_data):
    print("🧠 IA: Iniciando redacción...")
    
    prompt = f"""
    Eres el Editor Jefe de 'Radar Internacional'.
    NOTICIA: {story_data}

    TAREA OBLIGATORIA:
    Escribe un REPORTAJE LARGO (4 párrafos) en ESPAÑOL NEUTRO.
    
    FORMATO DE SALIDA (Usa el separador ||||):
    TITULO_PROFESIONAL||||KEYWORD_FOTO_INGLES||||CONTENIDO_HTML

    REGLAS:
    1. KEYWORD_FOTO: Descripción visual en inglés (ej: "Joe Biden speech, photorealistic").
    2. HTML: Usa <p>, <b> y <blockquote>.
    3. NO uses Markdown.
    """
    
    # Llamamos al cazador
    result = call_ai_hunter(prompt)
    
    if not result:
        return None

    try:
        texto = result['candidates'][0]['content']['parts'][0]['text']
        texto = texto.replace("```html", "").replace("```", "").strip()
        parts = texto.split("||||")
        
        if len(parts) >= 3:
            return {
                "titulo": parts[0].strip(),
                "foto_prompt": parts[1].strip(),
                "contenido": parts[2].strip()
            }
        else:
            return None 
    except:
        return None

# --- 4. PUBLICAR ---
def publish(article):
    if not article:
        print("❌ No se generó artículo.")
        sys.exit(1)

    print(f"🚀 Publicando: {article['titulo']}")
    
    try:
        # FOTO REALISTA (Pollinations)
        prompt_foto = urllib.parse.quote(article['foto_prompt'])
        # Añadimos un número aleatorio (seed) para que la foto siempre sea nueva
        seed = random.randint(1, 9999)
        img_url = f"https://image.pollinations.ai/prompt/news%20photo%20{prompt_foto}?width=800&height=450&nologo=true&model=flux&seed={seed}"
        
        html = f"""
        <div style="font-family: 'Georgia', serif; font-size: 19px; line-height: 1.8; color:#222;">
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 25px;">
                <img border="0" src="{img_url}" style="width:100%; max-width:800px; border-radius:5px;" alt="Imagen de la noticia"/>
            </div>
            {article['contenido']}
            <br><hr>
            <p style="font-size:12px; color:#666; text-align:center;">Radar Internacional © 2026</p>
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
