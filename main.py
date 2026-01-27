import feedparser
import google.generativeai as genai
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
import json
import sys

print("🕵️ INICIANDO DIAGNÓSTICO DE RADAR INTERNACIONAL...")

# 1. VERIFICAR VARIABLES
try:
    BLOG_ID = os.environ["BLOG_ID"]
    print(f"✅ ID del Blog detectada: {BLOG_ID}")
    
    token_content = os.environ["GOOGLE_TOKEN"]
    print("✅ Token de Google detectado.")
    
    # Intentar cargar credenciales
    token_info = json.loads(token_content)
    creds = Credentials.from_authorized_user_info(token_info)
    print("✅ Credenciales decodificadas correctamente.")
    
    service = build('blogger', 'v3', credentials=creds)
    print("✅ Conexión con Blogger establecida (API Service creada).")

except Exception as e:
    print(f"❌ ERROR FATAL EN CREDENCIALES: {e}")
    sys.exit(1) # Esto forzará la X roja

# 2. PRUEBA DE ACCESO A BLOGGER (La prueba de fuego)
try:
    print(f"🔍 Buscando el blog con ID: {BLOG_ID}...")
    blog = service.blogs().get(blogId=BLOG_ID).execute()
    print(f"🎉 ¡CONEXIÓN EXITOSA! Nombre del blog encontrado: '{blog['name']}'")
    print(f"    URL del blog: {blog['url']}")
except Exception as e:
    print(f"❌ ERROR CONECTANDO AL BLOG: {e}")
    print("⚠️ REVISA QUE LA 'BLOG_ID' EN LOS SECRETOS DE GITHUB SEA SOLO NUMEROS.")
    sys.exit(1)

# 3. PRUEBA DE IA (GEMINI PRO)
try:
    print("🧠 Probando Gemini Pro...")
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Di solo la palabra: Funcionando")
    print(f"✅ Respuesta de IA: {response.text}")
except Exception as e:
    print(f"❌ ERROR CON LA IA: {e}")
    sys.exit(1)

# 4. INTENTO DE PUBLICACIÓN DE PRUEBA
try:
    print("🚀 Intentando publicar entrada de prueba...")
    body = {
        "kind": "blogger#post",
        "title": "PRUEBA TÉCNICA - PUEDES BORRAR ESTO",
        "content": "<p>Si lees esto, el sistema funciona al 100%.</p>",
        "labels": ["Sistema"]
    }
    posts = service.posts()
    result = posts.insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
    print(f"✅ ¡PUBLICADO! URL: {result.get('url')}")

except Exception as e:
    print(f"❌ ERROR PUBLICANDO: {e}")
    sys.exit(1)

print("🏁 DIAGNÓSTICO FINALIZADO CON ÉXITO.")
