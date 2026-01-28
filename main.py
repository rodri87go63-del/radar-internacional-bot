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

print("🔥 INICIANDO PROTOCOLO DE REDACCIÓN AVANZADA...")

# --- 1. CONFIGURACIÓN ---
# Fuentes en español
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
    print(f"❌ Error Credenciales: {e}")
    sys.exit(1)

# --- 2. OBTENER DATOS (O GENERAR RESPALDO) ---
def get_news_data():
    print("📡 Intentando conectar con agencias de noticias...")
    combined_text = ""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        for url in RSS_URLS:
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req) as response:
                    feed = feedparser.parse(response.read())
                
                # Tomamos solo la primera de cada medio para enfocar el tema
                if feed.entries:
                    item = feed.entries[0]
                    combined_text += f"TITULAR: {item.title}. RESUMEN: {item.summary}\n"
            except:
                continue
    except Exception as e:
        print(f"⚠️ Error de conexión RSS: {e}")

    # SI NO HAY NOTICIAS (BLOQUEO), USAMOS TEMA DE RESPALDO
    if len(combined_text) < 50:
        print("⚠️ No se pudieron leer noticias. Generando tema de análisis global...")
        fecha = time.strftime("%d/%m/%Y")
        combined_text = f"Realizar un análisis geopolítico sobre la situación económica y política mundial a fecha de {fecha}. Tensiones internacionales y mercados."
    
    return combined_text

# --- 3. REDACCIÓN EXTENSA (FORMATO SEGURO) ---
def generate_article(info_base):
    print("🧠 IA: Redactando reportaje de investigación (Largo)...")
    
    prompt = f"""
    Actúa como Periodista Senior de 'Radar Internacional'.
    
    INFORMACIÓN BASE:
    {info_base}

    OBJETIVO:
    Escribe un ARTÍCULO DE FONDO (Reportaje) en ESPAÑOL NEUTRO.
    Debe parecer escrito por un humano, serio y profesional.
    
    REQUISITOS OBLIGATORIOS:
    1. **Extensión:** MÍNIMO 500 PALABRAS. 
    2. **Estructura:**
       - Título: Periodístico y atractivo (Sin números).
       - Cuerpo: 4 o 5 párrafos largos.
       - Negritas: Usa <b> para resaltar nombres y datos clave.
    3. **Imagen:** Dame 1 sola palabra clave en INGLÉS para la foto (ej: "Politics", "Economy", "War", "City").

    FORMATO DE RESPUESTA (Usa el separador |||):
    TITULO|||PALABRA_CLAVE_FOTO|||CONTENIDO_HTML

    El contenido HTML debe usar etiquetas <p>, <h3> para subtítulos y <blockquote> para citas.
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        parts = text.split("|||")
        
        if len(parts) >= 3:
            return {
                "titulo": parts[0].strip(),
                "keyword": parts[1].strip(),
                "contenido": parts[2].strip()
            }
        else:
            raise Exception("Formato inválido")
            
    except Exception as e:
        print(f"⚠️ Error IA: {e}. Usando texto simple.")
        # RESCATE: Si la IA falla el formato, publicamos texto plano
        ts = int(time.time())
        return {
            "titulo": "Informe de Actualidad Internacional",
            "keyword": "news",
            "contenido": f"<p><b>REDACCIÓN (Radar) —</b><br>Informe especial. Se analizan los siguientes puntos:<br>{info_base[:500]}...</p>"
        }

# --- 4. PUBLICAR (FOTOS FILTRADAS) ---
def publish(article):
    print(f"🚀 Publicando: {article['titulo']}")
    
    try:
        # FOTO REAL FILTRADA (Evita gatos/cosas raras)
        # Forzamos categorías serias
        kw = article['keyword'].lower().replace(" ", "")
        safe_keywords = f"{kw},news,politics,business" # Añadimos contexto para asegurar seriedad
        
        ts = int(time.time())
        img_url = f"https://loremflickr.com/800/450/{safe_keywords}/all?lock={ts}"
        
        html = f"""
        <div style="font-family: 'Georgia', serif; font-size: 19px; color: #111; line-height: 1.8; max-width: 100%;">
            
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 30px;">
                <img border="0" src="{img_url}" style="width:100%; border-radius:3px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);" alt="Imagen de actualidad"/>
                <br/><small style="font-family:Arial,sans-serif; font-size:10px; color:#666;">FOTOGRAFÍA DE ARCHIVO: {kw.upper()}</small>
            </div>

            <div style="text-align: justify;">
                <p><span style="background-color: #000; color: #fff; padding: 2px 6px; font-size: 12px; font-family: Arial; font-weight: bold; text-transform: uppercase;">Radar Internacional</span> <b>—</b></p>
                {article['contenido']}
            </div>

            <div style="margin-top: 40px; border-top: 1px solid #ccc; padding-top: 10px;">
                <p style="font-family: Arial, sans-serif; font-size: 12px; color: #888;">
                    <i>Este artículo ha sido redactado por el equipo de análisis de Radar Internacional basándose en reportes de agencias globales.</i>
                </p>
            </div>
        </div>
        """
        
        body = {
            "kind": "blogger#post",
            "title": article["titulo"],
            "content": html,
            "labels": ["Mundo", "Noticias", "Portada"]
        }
        
        service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print("✅ ¡NOTICIA PUBLICADA CORRECTAMENTE!")
        
    except Exception as e:
        print(f"❌ Error publicando: {e}")
        sys.exit(1)

if __name__ == "__main__":
    datos = get_news_data()
    art = generate_article(datos)
    publish(art)
