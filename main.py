import feedparser
import google.generativeai as genai
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
import json
import random
import time
import sys
import urllib.parse

# --- 1. CONFIGURACIÓN ---
RSS_URLS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.rt.com/rss/news/"
]

try:
    token_info = json.loads(os.environ["GOOGLE_TOKEN"])
    creds = Credentials.from_authorized_user_info(token_info)
    service = build('blogger', 'v3', credentials=creds)
    BLOG_ID = os.environ["BLOG_ID"]
    
    # USAMOS EL MODELO FLASH (Es el que funciona con tu librería actual)
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"Error config: {e}")
    sys.exit(1)

# --- 2. OBTENER INFORMACIÓN ---
def get_latest_news():
    print("📡 Leyendo cables de noticias...")
    news_pool = []
    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:4]:
                # Limpiamos el texto para que no sea muy largo
                summary = entry.summary if 'summary' in entry else entry.title
                news_pool.append(f"- {entry.title}: {summary[:200]}...")
        except:
            pass
    random.shuffle(news_pool)
    return "\n".join(news_pool[:12])

# --- 3. REDACCIÓN PERIODÍSTICA (IA) ---
def generate_article(raw_data):
    print("🧠 IA redactando artículo completo...")
    
    prompt = f"""
    Eres el Jefe de Redacción de un medio internacional serio.
    Información recibida:
    {raw_data}

    Instrucciones:
    1. Identifica el tema MÁS IMPORTANTE Y ACTUAL de la lista.
    2. Escribe un artículo de noticias COMPLETO (mínimo 300 palabras).
    3. Usa un tono formal, objetivo y periodístico.
    
    ESTRUCTURA JSON REQUERIDA:
    {{
        "titulo": "ESCRIBE UN TITULO IMPACTANTE AQUI",
        "contenido": "TODO EL CODIGO HTML DEL ARTICULO AQUI",
        "etiquetas": ["Internacional", "Noticias"]
    }}
    
    REGLAS PARA EL HTML (contenido):
    - Empieza con: <p><b>REDACCIÓN INTERNACIONAL (Radar) —</b> [Primer párrafo resumen]</p>
    - Usa varios párrafos <p> para desarrollar la noticia.
    - Usa un subtítulo <h2> a la mitad.
    - Incluye un dato clave en un <blockquote>.
    - NO incluyas el título H1 dentro del contenido.
    - NO uses markdown (```), solo JSON puro.
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"⚠️ Error IA: {e}. Reintentando...")
        return None

# --- 4. PUBLICACIÓN CON FOTO IA ---
def publish(article):
    if not article: return
    
    print(f"🚀 Publicando: {article['titulo']}")
    
    # Generar imagen IA basada en el título (Pollinations)
    titulo_seguro = urllib.parse.quote(article['titulo'])
    img_url = f"https://image.pollinations.ai/prompt/news%20photo%20realistic%20{titulo_seguro}?width=800&height=450&nologo=true"
    
    # HTML Final
    html_content = f"""
    <div class="separator" style="clear: both; text-align: center; margin-bottom: 20px;">
        <img border="0" src="{img_url}" style="width: 100%; max-width: 800px; border-radius: 5px; box-shadow: 0 5px 15px rgba(0,0,0,0.1);" />
        <br/><small style="color:#888;">Imagen generada por IA para contexto noticioso</small>
    </div>
    {article['contenido']}
    <br><hr>
    <p style="text-align:center; font-size:12px; color:#999;">
        <i>Radar Internacional - Monitoreo automatizado de prensa global.</i>
    </p>
    """
    
    body = {
        "kind": "blogger#post",
        "title": article["titulo"],
        "content": html_content,
        "labels": article.get("etiquetas", ["Noticias"])
    }
    
    try:
        service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print("✅ ¡NOTICIA PUBLICADA CORRECTAMENTE!")
    except Exception as e:
        print(f"❌ Error final: {e}")

if __name__ == "__main__":
    data = get_latest_news()
    if data:
        art = generate_article(data)
        publish(art)
    else:
        print("No hay datos suficientes.")
