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

print("🚀 INICIANDO RADAR (MODO AUTO-DETECT)...")

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
    print("✅ Credenciales cargadas.")
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
            
            for entry in feed.entries[:6]:
                # Buscamos noticias con algo de texto
                summary = entry.summary if hasattr(entry, 'summary') else entry.title
                if len(summary) > 25:
                    candidates.append(f"TITULAR: {entry.title}\nRESUMEN: {summary}")
        except:
            pass
            
    if not candidates:
        return None
    return random.choice(candidates)

# --- 3. AUTO-DETECTAR MODELO DE IA ---
def get_working_model_url():
    # Preguntamos a Google qué modelos permite usar con esta llave
    url_list = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    try:
        resp = requests.get(url_list)
        data = resp.json()
        
        # Buscamos el mejor modelo disponible (Flash o Pro)
        for model in data.get('models', []):
            name = model['name']
            if 'gemini-1.5-flash' in name:
                print(f"✅ Modelo detectado: {name}")
                return f"https://generativelanguage.googleapis.com/v1beta/{name}:generateContent?key={API_KEY}"
            if 'gemini-pro' in name:
                print(f"✅ Modelo detectado: {name}")
                return f"https://generativelanguage.googleapis.com/v1beta/{name}:generateContent?key={API_KEY}"
                
        print("⚠️ No se detectó modelo preferido, usando default...")
        return f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    except:
        return f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

# --- 4. REDACCIÓN ---
def write_full_article(story_data):
    print("🧠 IA: Redactando reportaje...")
    
    api_url = get_working_model_url()
    
    prompt = f"""
    Eres 'Radar Internacional'.
    NOTICIA: {story_data}

    TAREA:
    Escribe un REPORTAJE LARGO (4 párrafos) en ESPAÑOL NEUTRO.
    
    ESTRUCTURA DE SALIDA (Usa el separador ||||):
    TITULO_PROFESIONAL||||PROMPT_FOTO_INGLES||||CONTENIDO_HTML

    REGLAS:
    1. El PROMPT_FOTO debe ser una descripción visual en inglés (ej: "Donald Trump speaking at podium, photorealistic").
    2. HTML: Usa <p>, <b> y citas. No Markdown.
    """
    
    payload = { "contents": [{ "parts": [{"text": prompt}] }] }
    
    try:
        response = requests.post(api_url, json=payload)
        result = response.json()
        
        if "error" in result:
            print(f"❌ Error Google: {result['error']['message']}")
            return None

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
    except Exception as e:
        print(f"⚠️ Error IA: {e}")
        return None

# --- 5. PUBLICAR ---
def publish(article):
    if not article:
        print("❌ No hay artículo.")
        sys.exit(1)

    print(f"🚀 Publicando: {article['titulo']}")
    
    try:
        # FOTO REALISTA VIA POLLINATIONS (Mejor calidad que Flickr)
        # Usamos el prompt visual detallado que nos dio la IA
        foto_prompt = urllib.parse.quote(article['foto_prompt'])
        img_url = f"https://image.pollinations.ai/prompt/news%20photo%20{foto_prompt}?width=800&height=450&nologo=true&model=flux"
        
        html = f"""
        <div style="font-family: 'Georgia', serif; font-size: 19px; line-height: 1.8; color:#111;">
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 25px;">
                <img border="0" src="{img_url}" style="width:100%; max-width:800px; border-radius:5px; box-shadow:0 5px 15px rgba(0,0,0,0.1);" alt="Imagen de la noticia"/>
            </div>
            {article['contenido']}
            <br><hr>
            <p style="font-size:12px; color:#666;">Radar Internacional © 2026</p>
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
