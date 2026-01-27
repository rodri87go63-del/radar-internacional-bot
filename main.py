import feedparser
import google.generativeai as genai
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
import json
import random
import time
import sys

print("🔥 INICIANDO MODO TANQUE DE GUERRA...")

# --- 1. CONFIGURACIÓN ---
RSS_URLS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.rt.com/rss/news/"
]

try:
    # Cargar credenciales
    token_info = json.loads(os.environ["GOOGLE_TOKEN"])
    creds = Credentials.from_authorized_user_info(token_info)
    service = build('blogger', 'v3', credentials=creds)
    BLOG_ID = os.environ["BLOG_ID"]
    
    # Configurar IA (Volvemos al PRO clásico que nunca falla)
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
    print("✅ Credenciales configuradas.")
except Exception as e:
    print(f"❌ ERROR CRÍTICO DE CONFIGURACIÓN: {e}")
    sys.exit(1)

# --- 2. OBTENER NOTICIAS ---
def get_latest_news():
    print("📡 Leyendo noticias...")
    news_pool = []
    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                print(f"   -> {url}: OK ({len(feed.entries)} noticias)")
                for entry in feed.entries[:2]:
                    news_pool.append(f"- {entry.title}")
            else:
                print(f"   -> {url}: Vacío")
        except:
            print(f"   -> {url}: Falló")
            
    if not news_pool:
        print("❌ NO SE ENCONTRARON NOTICIAS EN NINGÚN LADO.")
        # Para probar, inventamos una si falla todo
        news_pool = ["El mercado global se estabiliza", "Nuevas tecnologías en IA"]
    
    return "\n".join(news_pool[:10])

# --- 3. GENERAR ARTÍCULO (CON PLAN B) ---
def generate_article(raw_data):
    print("🧠 IA Trabajando...")
    prompt = f"""
    Actúa como 'Radar Internacional'. Redacta una noticia corta basada en:
    {raw_data}
    
    IMPORTANTE: Devuelve SOLO un objeto JSON válido.
    {{
        "titulo": "TITULO AQUÍ",
        "contenido": "<p>Texto de la noticia aquí...</p>",
        "etiquetas": ["Mundo"]
    }}
    """
    try:
        response = model.generate_content(prompt)
        # Limpieza agresiva
        texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(texto_limpio)
    except Exception as e:
        print(f"⚠️ La IA no devolvió JSON perfecto. Error: {e}")
        print("⚠️ Usando PLAN B (Publicar texto plano)...")
        # Si falla el JSON, devolvemos un objeto manual con el texto crudo
        return {
            "titulo": "RESUMEN DE ACTUALIDAD (Radar Internacional)",
            "contenido": f"<p>{response.text}</p>",
            "etiquetas": ["Flash", "Mundo"]
        }

# --- 4. PUBLICAR ---
def publish(article):
    print(f"🚀 Publicando: {article['titulo']}...")
    try:
        # Imagen aleatoria
        kw = random.choice(["news", "world", "tech"])
        img = f"https://source.unsplash.com/800x400/?{kw}&t={int(time.time())}"
        html_img = f'<div style="text-align:center"><img src="{img}" style="width:100%"/></div><br/>'
        
        body = {
            "kind": "blogger#post",
            "title": article["titulo"],
            "content": html_img + article["contenido"],
            "labels": article.get("etiquetas", ["Noticias"])
        }
        
        res = service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print(f"🎉 ¡PUBLICADO! Link: {res.get('url')}")
    except Exception as e:
        print(f"❌ ERROR PUBLICANDO EN BLOGGER: {e}")
        sys.exit(1)

# --- EJECUCIÓN ---
if __name__ == "__main__":
    datos = get_latest_news()
    articulo = generate_article(datos)
    publish(articulo)
