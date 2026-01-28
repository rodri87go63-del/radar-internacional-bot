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

print("📰 INICIANDO REDACCIÓN EXTENSA (SISTEMA SIN JSON)...")

# --- 1. FUENTES ---
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

# --- 2. SELECCIONAR NOTICIA ---
def get_single_news_item():
    print("📡 Buscando noticia principal...")
    candidates = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for url in RSS_URLS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                feed = feedparser.parse(response.read())
            
            for entry in feed.entries[:6]:
                if len(entry.title) > 10: # Evitar vacíos
                    candidates.append(f"{entry.title}. {entry.summary if hasattr(entry, 'summary') else ''}")
        except:
            pass
            
    if not candidates:
        return None
    
    # Seleccionamos una al azar para variar
    return random.choice(candidates)

# --- 3. REDACCIÓN SIN LÍMITES (FORMATO |||) ---
def generate_article(news_text):
    print("🧠 IA: Escribiendo artículo largo...")
    
    # ESTRATEGIA: Usamos separadores ||| que son indestructibles
    prompt = f"""
    Eres un Periodista Senior de 'Radar Internacional'.
    
    NOTICIA A DESARROLLAR:
    {news_text}

    TU TAREA:
    Escribe un ARTÍCULO DE ANÁLISIS PROFUNDO Y EXTENSO sobre este tema.
    
    REGLAS OBLIGATORIAS:
    1. **Extensión:** MÍNIMO 500 PALABRAS. Quiero 4 o 5 párrafos bien desarrollados.
    2. **Estructura:**
       - Párrafo 1: Introducción fuerte con negritas en datos clave.
       - Párrafo 2 y 3: Desarrollo, contexto histórico, reacciones.
       - Párrafo 4: Conclusión o proyección futura.
    3. **Formato:** HTML limpio (<p>, <b>, <blockquote>).
    
    FORMATO DE RESPUESTA (IMPORTANTE):
    Debes devolver los datos separados EXACTAMENTE por tres barras verticales "|||".
    
    Ejemplo de salida:
    TITULO DE LA NOTICIA|||keyword, english|||<p>Párrafo 1...</p><p>Párrafo 2...</p>
    
    AHORA TÚ (Solo la respuesta con los |||):
    """
    
    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        
        # Limpiamos por si la IA pone markdown
        raw_text = raw_text.replace("```", "").replace("html", "")
        
        # Separamos las partes
        partes = raw_text.split("|||")
        
        if len(partes) < 3:
            # Si falló el formato, intentamos salvar el contenido
            print("⚠️ Formato imperfecto, intentando recuperar texto...")
            return {
                "titulo": "Informe Especial: Actualidad Global",
                "keywords": "news, world",
                "contenido": f"{raw_text}" # Publicamos todo lo que haya escrito
            }
            
        return {
            "titulo": partes[0].strip(),
            "keywords": partes[1].strip(),
            "contenido": partes[2].strip()
        }
        
    except Exception as e:
        print(f"⚠️ Error IA: {e}")
        return None

# --- 4. PUBLICAR ---
def publish(article):
    if not article: return
    print(f"🚀 Publicando: {article['titulo']}")
    
    try:
        # Foto Real
        tags = article['keywords'].replace(" ", "").replace(",", ",")
        ts = int(time.time())
        img_url = f"https://loremflickr.com/800/450/{tags}/all?lock={ts}"
        
        html = f"""
        <div style="font-family: 'Georgia', serif; font-size: 18px; color: #222; line-height: 1.8;">
            
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 30px;">
                <img border="0" src="{img_url}" style="width:100%; max-width:800px; border-radius:4px;" alt="Imagen relacionada"/>
                <br/>
                <small style="font-family:Arial; font-size:10px; color:#666;">ARCHIVO: {tags.upper()}</small>
            </div>

            <div style="margin-bottom: 30px;">
                <p><b>REDACCIÓN INTERNACIONAL (Radar) —</b></p>
                {article['contenido']}
            </div>

            <div style="background-color:#f5f5f5; padding:15px; border-left:4px solid #333; font-family:Arial,sans-serif; font-size:14px;">
                <b>Nota del Editor:</b> Este artículo analiza los eventos más recientes basándose en reportes de agencias internacionales. La situación está en desarrollo.
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
        print("✅ ¡NOTICIA LARGA PUBLICADA!")
        
    except Exception as e:
        print(f"❌ Error Publicando: {e}")
        sys.exit(1)

if __name__ == "__main__":
    noticia = get_single_news_item()
    if noticia:
        art = generate_article(noticia)
        publish(art)
    else:
        print("❌ Error RSS")
