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

print("📰 INICIANDO REDACCIÓN DE REPORTAJE A FONDO...")

# --- 1. CONFIGURACIÓN ---
# Usamos BBC Mundo y El País porque tienen los resúmenes más completos
RSS_URLS = [
    "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada",
    "https://www.bbc.com/mundo/temas/internacional/index.xml"
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

# --- 2. SELECCIONAR UNA (1) SOLA NOTICIA ---
def get_one_story():
    print("📡 Buscando la historia más relevante...")
    candidates = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for url in RSS_URLS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                feed = feedparser.parse(response.read())
            
            # Filtramos: Solo noticias que tengan algo de texto en el resumen
            for entry in feed.entries[:6]:
                summary = entry.summary if hasattr(entry, 'summary') else entry.title
                if len(summary) > 30: 
                    candidates.append(f"TITULAR: {entry.title}\nDATOS: {summary}")
        except:
            pass
            
    if not candidates:
        return None
    
    # Elegimos UNA al azar para que no se repita siempre la primera
    story = random.choice(candidates)
    print(f"🎯 Historia seleccionada:\n{story[:50]}...")
    return story

# --- 3. REDACCIÓN EXTENSA (FORMATO SEGURO) ---
def write_full_article(story_data):
    print("🧠 IA: Escribiendo 4 párrafos detallados...")
    
    # Este prompt obliga a la IA a inventar el contexto necesario para llenar espacio
    prompt = f"""
    Eres un Periodista de Investigación de 'Radar Internacional'.
    
    BASADO EN ESTA NOTICIA:
    {story_data}

    TU TAREA:
    Escribe un ARTÍCULO COMPLETO Y LARGO. No hagas un resumen. Expande la información usando tus conocimientos sobre el contexto geopolítico de este tema.

    REQUISITOS ESTRICTOS:
    1. **LONGITUD:** Debes escribir EXACTAMENTE 4 PÁRRAFOS LARGOS.
    2. **FOTO:** Dame 1 sola palabra clave en INGLÉS que represente el SUJETO de la noticia (ej: si es sobre Trump, pon "Trump"; si es sobre Ucrania, pon "Ukraine"; si es economía, pon "Wall Street"). No uses palabras genéricas como "News".
    3. **ESTILO:** Serio, objetivo, profesional.
    4. **FORMATO DE SALIDA:** Usa el separador "||||" (cuatro barras) para separar el título, la keyword y el texto.

    ESTRUCTURA DE TU RESPUESTA (Sigue esto al pie de la letra):
    TITULO DE LA NOTICIA||||KEYWORD_FOTO||||<p><b>CIUDAD (Radar) —</b> Aquí empieza el primer párrafo largo...</p><p>Aquí va el segundo párrafo explicando antecedentes...</p><p>Aquí el tercer párrafo con reacciones...</p><p>Cuarto párrafo de conclusión.</p>
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Limpieza de basura que a veces pone la IA
        text = text.replace("```html", "").replace("```", "")
        
        # Cortamos el texto usando las 4 barras
        parts = text.split("||||")
        
        if len(parts) >= 3:
            return {
                "titulo": parts[0].strip(),
                "foto_keyword": parts[1].strip(),
                "contenido": parts[2].strip()
            }
        else:
            print("⚠️ La IA no usó el separador correcto. Reintentando limpieza...")
            # Intento de rescate si falla el formato
            return None 
            
    except Exception as e:
        print(f"❌ Error IA: {e}")
        return None

# --- 4. PUBLICAR ---
def publish(article):
    if not article:
        print("❌ No se pudo generar el artículo correctamente.")
        return

    print(f"🚀 Publicando: {article['titulo']}")
    
    try:
        # FOTO ESPECÍFICA (LoremFlickr)
        # Usamos la palabra clave específica que nos dio la IA (ej: "Trump", "Putin", "Bitcoin")
        tag = article['foto_keyword'].replace(" ", "")
        ts = int(time.time())
        # Pedimos foto grande
        img_url = f"https://loremflickr.com/800/500/{tag}/all?lock={ts}"
        
        html = f"""
        <div style="font-family: 'Georgia', serif; font-size: 18px; color: #222; line-height: 1.8;">
            
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 25px;">
                <img border="0" src="{img_url}" style="width:100%; max-width:800px; border-radius:5px;" alt="Imagen relacionada: {tag}"/>
                <br/><small style="font-family:Arial,sans-serif; font-size:11px; color:#666;">ARCHIVO: {tag.upper()}</small>
            </div>

            <div style="text-align: justify;">
                {article['contenido']}
            </div>

            <div style="margin-top: 30px; border-top: 1px solid #ccc; padding-top: 10px;">
                <p style="font-family: Arial, sans-serif; font-size: 13px; font-weight: bold;">
                    Radar Internacional
                </p>
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
        print("✅ ¡ÉXITO! Entrada creada.")
        
    except Exception as e:
        print(f"❌ Error publicando: {e}")
        sys.exit(1)

# --- EJECUCIÓN ---
if __name__ == "__main__":
    intentos = 0
    articulo = None
    
    # Intentamos hasta 3 veces si la IA falla el formato
    while intentos < 3 and not articulo:
        raw_story = get_one_story()
        if raw_story:
            articulo = write_full_article(raw_story)
        intentos += 1
        if not articulo:
            print("🔄 Reintentando generación...")
            time.sleep(2)
            
    if articulo:
        publish(articulo)
    else:
        print("❌ Fallaron todos los intentos. No se publica nada (para evitar errores).")
        # Forzamos error para que salga rojo en GitHub y sepas que falló
        sys.exit(1)
