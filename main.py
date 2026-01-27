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
import re

print("📰 INICIANDO REDACCIÓN DE ARTÍCULO DE FONDO...")

# --- 1. FUENTES DE NOTICIAS (ESPAÑOL) ---
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
    print(f"❌ Error Configuración: {e}")
    sys.exit(1)

# --- 2. SELECCIONAR UNA SOLA NOTICIA (ESTRATEGIA FRANCOTIRADOR) ---
def get_single_news_item():
    print("📡 Buscando la mejor historia del momento...")
    candidates = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for url in RSS_URLS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                feed = feedparser.parse(response.read())
            
            # Guardamos las noticias que tengan resumen para tener contexto
            for entry in feed.entries[:5]:
                if hasattr(entry, 'summary') and len(entry.summary) > 20:
                    candidates.append({
                        "titulo": entry.title,
                        "resumen": entry.summary,
                        "link": entry.link
                    })
        except:
            pass
            
    if not candidates:
        return None
    
    # Elegimos UNA noticia al azar de las candidatas para asegurar variedad
    # Esto evita que siempre coja la primera si se ejecuta seguido
    seleccionada = random.choice(candidates)
    print(f"🎯 Noticia seleccionada para reportaje: {seleccionada['titulo']}")
    return seleccionada

# --- 3. REDACCIÓN PROFESIONAL (4 PÁRRAFOS) ---
def generate_article(news_item):
    print("🧠 IA: Escribiendo reportaje extenso...")
    
    prompt = f"""
    Eres un Reportero Senior de 'Radar Internacional'.
    
    LA NOTICIA A DESARROLLAR ES:
    Titular: {news_item['titulo']}
    Contexto: {news_item['resumen']}

    TU TAREA:
    Escribe un ARTÍCULO COMPLETO en ESPAÑOL NEUTRO expandiendo esta información.
    
    REQUISITOS OBLIGATORIOS:
    1. **Título:** Un titular periodístico real y atractivo (SIN números, SIN "Informe #").
    2. **Extensión:** Mínimo 4 párrafos largos y bien explicados.
    3. **Formato:** Usa etiquetas HTML.
    4. **Estilo:** Usa **negritas (<b>)** para resaltar frases clave o nombres importantes en cada párrafo.
    5. **Keywords:** Dame 2 palabras clave en INGLÉS que describan la imagen visualmente (ej: "War, Tank" o "President, Podium").

    FORMATO DE SALIDA (Solo este JSON):
    {{
        "titulo_final": "Tu titular aquí",
        "contenido_html": "<p>Párrafo 1...</p><p>Párrafo 2...</p>...",
        "keywords_img": "keyword1, keyword2"
    }}
    
    NO uses Markdown. Solo JSON.
    """
    
    try:
        response = model.generate_content(prompt)
        # Limpieza de JSON
        texto = response.text.replace("```json", "").replace("```", "").strip()
        # A veces la IA falla un poco el JSON, intentamos limpiarlo
        inicio = texto.find("{")
        fin = texto.rfind("}") + 1
        json_str = texto[inicio:fin]
        
        return json.loads(json_str)
        
    except Exception as e:
        print(f"⚠️ Error IA: {e}. Usando modo manual.")
        # PLAN DE EMERGENCIA MEJORADO
        # Si la IA falla, usamos el titular REAL de la noticia, no un número.
        return {
            "titulo_final": news_item['titulo'],
            "contenido_html": f"""
                <p><b>REDACCIÓN INTERNACIONAL (Radar) —</b></p>
                <p>Informes recientes destacan que <b>{news_item['titulo']}</b>.</p>
                <p>{news_item['resumen']}</p>
                <p>Este evento marca un punto importante en la agenda global actual. Analistas internacionales sugieren que las implicaciones podrían ser significativas a corto plazo.</p>
                <p><i>Seguiremos ampliando esta información a medida que se desarrollen los hechos.</i></p>
            """,
            "keywords_img": "news, world"
        }

# --- 4. PUBLICAR ---
def publish(article):
    print(f"🚀 Publicando entrada: {article['titulo_final']}")
    
    try:
        # FOTO REAL
        tags = article['keywords_img'].replace(" ", "").replace(",", ",")
        ts = int(time.time())
        img_url = f"https://loremflickr.com/800/450/{tags}/all?lock={ts}"
        
        html = f"""
        <div style="font-family: 'Georgia', serif; font-size: 19px; color: #222; line-height: 1.8;">
            
            <!-- IMAGEN DESTACADA -->
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 30px;">
                <img border="0" src="{img_url}" style="width:100%; max-width:800px; border-radius:4px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);" alt="Imagen relacionada"/>
                <br/>
                <small style="font-family:Arial,sans-serif; font-size:11px; color:#666; text-transform:uppercase;">
                    Archivo: {article['keywords_img']}
                </small>
            </div>

            <!-- CUERPO DE LA NOTICIA -->
            <div style="margin-bottom: 20px;">
                {article['contenido_html']}
            </div>

            <!-- PIE DE PÁGINA -->
            <div style="margin-top:40px; border-top: 3px solid #000; padding-top:10px;">
                <p style="font-family:Arial,sans-serif; font-size:13px; font-weight:bold; color:#000;">
                    RADAR INTERNACIONAL
                </p>
            </div>
        </div>
        """
        
        body = {
            "kind": "blogger#post",
            "title": article["titulo_final"],
            "content": html,
            "labels": ["Mundo", "Noticias", "Actualidad"]
        }
        
        service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print("✅ ¡PUBLICADO CORRECTAMENTE!")
        
    except Exception as e:
        print(f"❌ Error al publicar: {e}")
        sys.exit(1)

# --- EJECUCIÓN ---
if __name__ == "__main__":
    noticia_base = get_single_news_item()
    if noticia_base:
        articulo_terminado = generate_article(noticia_base)
        publish(articulo_terminado)
    else:
        print("❌ No se pudieron leer fuentes RSS hoy.")
