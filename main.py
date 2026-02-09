import feedparser
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
import json
import random
import time
import sys
import urllib.parse
import requests 
import urllib.parse

print("🚀 INICIANDO RADAR (GEMINI DIRECTO + FOTO IA)...")

# --- 1. CONFIGURACIÓN ---
RSS_URLS = [
    "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada",
    "https://www.bbc.com/mundo/temas/internacional/index.xml",
    "https://www.bbc.com/mundo/temas/economia/index.xml",
    "https://www.bbc.com/mundo/temas/ciencia_y_tecnologia/index.xml"
]

try:
    token_info = json.loads(os.environ["GOOGLE_TOKEN"])
    creds = Credentials.from_authorized_user_info(token_info)
    service = build('blogger', 'v3', credentials=creds)
    BLOG_ID = os.environ["BLOG_ID"]
    API_KEY = os.environ["GEMINI_API_KEY"]

    # Credenciales Telegram
    TG_TOKEN = os.environ["TELEGRAM_TOKEN"]
    TG_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
    
    # URL directa a Gemini 3 Flash preview
    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={API_KEY}"
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
            # Usamos requests en lugar de urllib para ser más modernos
            resp = requests.get(url, headers=headers, timeout=10)
            feed = feedparser.parse(resp.content)
            
            for entry in feed.entries[:5]:
                summary = entry.summary if hasattr(entry, 'summary') else entry.title
                if len(summary) > 20:
                    candidates.append(f"TITULAR: {entry.title}\nDATOS: {summary}")
        except:
            pass
            
    if not candidates:
        return None
    return random.choice(candidates)

# --- 3. REDACCIÓN (AQUÍ ES DONDE TÚ MANDAS) ---
def write_full_article(story_data):
    print("🧠 IA: Redactando reportaje...")
    
    prompt = f"""
    Eres Periodista de 'Radar Internacional'.
    NOTICIA: {story_data}

   TU MISIÓN:
    Escribe un ARTÍCULO DE FONDO (Mínimo 4 párrafos largos) en ESPAÑOL NEUTRO.
    No hagas un resumen simple. Agrega contexto, antecedentes y análisis.

    REGLAS DE FORMATO:
    1. **Título:** Periodístico y serio.
    2. **Imagen:** Crea un PROMPT VISUAL en INGLÉS para generar una foto realista.
    
    REGLAS PARA EL PROMPT DE LA FOTO:
    - Debe ser en INGLÉS.
    - Describe la ESCENA, no el concepto. (Mal: "Economy". Bien: "A busy stock market graph on a monitor, blurred office background").
    - NO uses nombres de personas famosas (la IA las deforma). Usa descripciones (ej: "A senior politician in a suit giving a speech").
    - Añade al final: ", photorealistic, 8k, news photography style".
    3. **CATEGORÍA:** Elige una: "Mundo", "Economia", "Tecnologia", "Politica", "Sociedad".
    4. **UBICACIÓN:** Elige una de estas opciones EXACTAS (la que mejor encaje): "China", "EEUU", "Venezuela", "Rusia", "Europa", "África", "Asia", "América", "Oceanía", "Medio Oriente".

    5. **Texto:** Usa negritas (<b>) para resaltar lo importante.


    FORMATO DE SALIDA (Usa separador ||||):
    TITULO||||PROMPT_VISUAL_INGLES||||CATEGORIA||||UBICACION||||CONTENIDO_HTML

    REGLAS HTML:
    - Primer párrafo: <b>CIUDAD (Radar) —</b> ...
    - Usa <p> y <b>. No Markdown.
    """
    
    # CONFIGURACIÓN ANTI-CENSURA (IMPORTANTE)
    payload = {
        "contents": [{ "parts": [{"text": prompt}] }],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        response = requests.post(API_URL, json=payload)
        result = response.json()
        texto = result['candidates'][0]['content']['parts'][0]['text']
        
        texto = texto.replace("```html", "").replace("```", "").strip()
        parts = texto.split("||||")

        # VERIFICACIÓN DE ERROR (Para que no se rompa si falla)
        if 'candidates' not in result:
            print(f"⚠️ Google bloqueó la respuesta. Razón: {result.get('promptFeedback', 'Desconocida')}")
            return None

        texto = result['candidates'][0]['content']['parts'][0]['text']
        texto = texto.replace("```html", "").replace("```", "").strip()
        parts = texto.split("||||")


        
         # Ahora esperamos 5 partes (incluyendo la ubicación)
        if len(parts) >= 5:
            return {
                "titulo": parts[0].strip(),
                "foto_prompt": parts[1].strip(),
                "categoria": parts[2].strip(), # NUEVA VARIABLE
                "ubicacion": parts[3].strip(),
                "contenido": parts[4].strip()
            }
        else:
            return None 
    except Exception as e:
        print(f"⚠️ Error IA: {e}")
        return None


# --- 4. TELEGRAM (ENVIAR ARCHIVO DIRECTO) ---
def send_telegram_file(title, link, image_bytes, category):
    print("📲 Subiendo foto a Telegram...")
    try:
        caption = f"🚨 <b>{title}</b>\n\n" \
                  f"🌍 <i>Categoría: {category}</i>\n\n" \
                  f"👇 <b>Leer noticia completa:</b>\n{link}\n\n" \
                  f"📡 <i>Radar Internacional</i>"
        
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
        
        # Enviamos el archivo binario (multipart/form-data)
        files = {
            'photo': ('noticia.jpg', image_bytes, 'image/jpeg')
        }
        data = {
            'chat_id': TG_CHAT_ID,
            'caption': caption,
            'parse_mode': 'HTML'
        }
        
        requests.post(url, data=data, files=files)
        print("✅ Telegram enviado con éxito.")
    except Exception as e:
        print(f"⚠️ Error Telegram: {e}")


        
# --- 4. PUBLICAR CON FOTO IA GENERADA ---
def publish(article):
    if not article:
        print("❌ No hay artículo.")
        sys.exit(1)

    print(f"🚀 Generando Imagen y Publicando: {article['titulo']} - {article['ubicacion']}")
    
    try:
        # GENERACIÓN DE IMAGEN CON POLLINATIONS (MODELO FLUX)
        # Codificamos el prompt que nos dio Gemini para que sea una URL válida
        prompt_imagen = urllib.parse.quote(article['foto_prompt'])
        
        # Añadimos una semilla aleatoria para que la foto siempre sea distinta
        seed = random.randint(1, 99999)
        
        # Usamos el modelo por defecto que es más estable y rápido.
        img_url = f"https://image.pollinations.ai/prompt/{prompt_imagen}?width=800&height=450&nologo=true&seed={seed}"

         
        # 2. DESCARGAR LA IMAGEN (ESTO ES LO NUEVO)
        print("⬇️ Descargando imagen al servidor...")
        img_response = requests.get(img_url, timeout=30)
        
        if img_response.status_code == 200:
            image_bytes = img_response.content
            print("✅ Imagen descargada correctamente.")
        else:
            print("⚠️ Falló descarga de imagen, se usará URL.")
            image_bytes = None

        
        html = f"""
        <div style="font-family: 'Georgia', serif; font-size: 19px; line-height: 1.8; color:#111;">
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 25px;">
                <img border="0" src="{img_url}" style="width:100%; max-width:800px; border-radius:5px;" alt="Imagen generada por IA"/>
                <br/><small style="font-family:Arial; font-size:10px; color:#666;">IMAGEN DE LA NOTICIA</small>
            </div>
            {article['contenido']}
            <br><hr>
            <p style="font-size:12px; color:#666; text-align:center;">Radar Internacional © 2026</p>
        </div>
        """
        # AQUI AGREGAMOS LA CATEGORÍA DINÁMICA
        etiquetas = ["Portada", article['categoria'], article['ubicacion']]
        
        body = {
            "kind": "blogger#post",
            "title": article["titulo"],
            "content": html,
            "labels": etiquetas
        }
        
        # 1. Publicar en Blogger
        response = service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        blog_link = response.get('url') # Obtenemos el link de la noticia nueva
        print(f"✅ Blog OK: {blog_link}")
        
        # 4. PUBLICAR EN TELEGRAM (Enviando el archivo descargado)
        if image_bytes:
            send_telegram_file(article['titulo'], blog_link, image_bytes, article['categoria'])
        else:
            # Si falló la descarga, enviamos solo texto para no romper nada
            print("⚠️ Enviando solo texto a Telegram por fallo de imagen.")
        
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
